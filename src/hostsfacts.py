import json
import os
import time
import shutil
from typing import Dict, Any, Iterable, List, Union

import ansible_runner

from mc.config import DATA_DIR, RESOURCES_DIR
from mc.db.mongodb import get_mongo_collection

# ---------- Tunable thresholds ----------
THRESHOLDS = {
    "disk_free_warn_pct": 20,  # % free
    "disk_free_crit_pct": 10,  # % free
    "inode_free_warn_pct": 15,  # % free
    "inode_free_crit_pct": 5,  # % free
    "mem_free_warn_pct": 10,  # % of total (nocache)
    "mem_free_crit_pct": 5,  # % of total (nocache)
    "swap_used_warn_pct": 25,  # % used
    "swap_used_crit_pct": 50,  # % used
    "load_warn_per_cpu": 1.0,  # 5m load / CPU
    "load_crit_per_cpu": 2.0,  # 5m load / CPU
    "min_ram_for_no_swap_mb": 4096,  # warn if no swap and low RAM
}

# Filesystem types that we typically ignore for space checks
IGNORED_FS_TYPES = {
    "tmpfs", "devtmpfs", "proc", "sysfs", "cgroup", "cgroup2",  # "squashfs",
    "overlay"  # comment out if you DO want to check container overlays
}


def _emit(issues: List[Dict[str, str]], name: str, severity: str, msg: str, host: str = None):
    prefix = f"[{host}] " if host else ""
    issues.append({
        "check_name": name,
        "severity": severity,
        "message": prefix + msg
    })


def _pct(part: float, whole: float) -> float:
    try:
        if whole <= 0:
            return 0.0
        return (part / whole) * 100.0
    except Exception:
        return 0.0


def _as_int(d: Dict[str, Any], *path, default=None) -> Union[int, None]:
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    try:
        return int(cur)
    except Exception:
        return default


def _get_cpu_count(f: Dict[str, Any]) -> int:
    # Prefer ansible_facts keys if nested
    af = f.get("ansible_facts", f)
    return (
            _as_int(af, "processor_vcpus") or
            _as_int(af, "processor_count") or
            _as_int(af, "ansible_processor_vcpus") or
            len(af.get("processor", [])) or
            1
    )


def _get_load5(f: Dict[str, Any]) -> float:
    af = f.get("ansible_facts", f)
    la = af.get("loadavg") or af.get("ansible_loadavg") or {}
    val = la.get("5m") or la.get("ansible_loadavg_5") or la.get("5")
    try:
        return float(val)
    except Exception:
        # Fallback: try 1m if 5m missing
        val = la.get("1m") or la.get("1")
        return float(val) if val is not None else 0.0


def _check_load(facts: Dict[str, Any], issues: List[Dict[str, str]], host: str = None):
    cpus = max(1, _get_cpu_count(facts))
    load5 = _get_load5(facts)
    per_cpu = load5 / cpus
    if per_cpu >= THRESHOLDS["load_crit_per_cpu"]:
        _emit(issues, "cpu_load_high", "critical",
              f"5-min load {load5:.2f} across {cpus} CPU(s) (={per_cpu:.2f}/CPU) exceeds {THRESHOLDS['load_crit_per_cpu']}/CPU.",
              host)
    elif per_cpu >= THRESHOLDS["load_warn_per_cpu"]:
        _emit(issues, "cpu_load_high", "warning",
              f"5-min load {load5:.2f} across {cpus} CPU(s) (={per_cpu:.2f}/CPU) exceeds {THRESHOLDS['load_warn_per_cpu']}/CPU.",
              host)


def _check_memory(facts: Dict[str, Any], issues: List[Dict[str, str]], host: str = None):
    af = facts.get("ansible_facts", facts)
    mem = af.get("memory_mb") or af.get("ansible_memory_mb") or {}
    real = mem.get("nocache") or mem.get("real") or {}
    total = _as_int(real, "total", default=_as_int(mem, "real", "total", default=None))
    free = _as_int(real, "free", default=_as_int(mem, "real", "free", default=None))
    if total and free is not None:
        free_pct = _pct(free, total)
        if free_pct <= THRESHOLDS["mem_free_crit_pct"]:
            _emit(issues, "memory_low", "critical",
                  f"Low free RAM (nocache): {free}MB of {total}MB ({free_pct:.1f}% free).", host)
        elif free_pct <= THRESHOLDS["mem_free_warn_pct"]:
            _emit(issues, "memory_low", "warning",
                  f"Low free RAM (nocache): {free}MB of {total}MB ({free_pct:.1f}% free).", host)

    # Swap usage
    swap = mem.get("swap") or {}
    st = _as_int(swap, "total", default=None)
    sf = _as_int(swap, "free", default=None)
    if st and sf is not None and st > 0:
        used = st - sf
        used_pct = _pct(used, st)
        if used_pct >= THRESHOLDS["swap_used_crit_pct"]:
            _emit(issues, "swap_heavily_used", "critical",
                  f"Swap usage high: {used}MB/{st}MB ({used_pct:.1f}% used).", host)
        elif used_pct >= THRESHOLDS["swap_used_warn_pct"]:
            _emit(issues, "swap_heavily_used", "warning",
                  f"Swap usage elevated: {used}MB/{st}MB ({used_pct:.1f}% used).", host)
    elif (st in (0, None)) and total and total < THRESHOLDS["min_ram_for_no_swap_mb"]:
        _emit(issues, "no_swap_with_low_ram", "warning",
              f"No swap configured and RAM is only {total}MB.", host)


def _check_disks(facts: Dict[str, Any], issues: List[Dict[str, str]], host: str = None):
    af = facts.get("ansible_facts", facts)
    mounts: Iterable[Dict[str, Any]] = af.get("mounts") or af.get("ansible_mounts") or []
    for m in mounts:
        fstype = m.get("fstype")
        if fstype in IGNORED_FS_TYPES:
            continue
        mp = m.get("mount") or m.get("mount_point") or m.get("device") or "?"
        # skip snap mounts
        if mp and mp.startswith("/snap/"):
            continue

        total = m.get("size_total") or 0
        avail = m.get("size_available") or 0
        inodes_total = m.get("inode_total") or 0
        inodes_available = m.get("inode_available") or 0

        # Disk space
        free_pct = _pct(avail, total)
        if total > 0:
            if free_pct <= THRESHOLDS["disk_free_crit_pct"]:
                _emit(issues, "disk_space", "critical",
                      f"Filesystem {mp} has only {free_pct:.1f}% free.", host)
            elif free_pct <= THRESHOLDS["disk_free_warn_pct"]:
                _emit(issues, "disk_space", "warning",
                      f"Filesystem {mp} has {free_pct:.1f}% free.", host)
            else:
                _emit(issues, "disk_space", "info",
                      f"Filesystem {mp} has {free_pct:.1f}% free.", host)

        # Inodes
        if inodes_total and inodes_available is not None:
            inode_free_pct = _pct(inodes_available, inodes_total)
            if inode_free_pct <= THRESHOLDS["inode_free_crit_pct"]:
                _emit(issues, "inode_exhaustion", "critical",
                      f"Filesystem {mp} has only {inode_free_pct:.1f}% free inodes.", host)
            elif inode_free_pct <= THRESHOLDS["inode_free_warn_pct"]:
                _emit(issues, "inode_exhaustion", "warning",
                      f"Filesystem {mp} has {inode_free_pct:.1f}% free inodes.", host)
            else:
                _emit(issues, "inode_exhaustion", "info",
                      f"Filesystem {mp} has {inode_free_pct:.1f}% free inodes.", host)


def _check_network(facts: Dict[str, Any], issues: List[Dict[str, str]], host: str = None):
    af = facts.get("ansible_facts", facts)
    ipv4 = af.get("default_ipv4") or af.get("ansible_default_ipv4") or {}
    addr = ipv4.get("address")
    gw = ipv4.get("gateway")
    if not addr:
        _emit(issues, "no_primary_ipv4", "critical", "No primary IPv4 address detected.", host)
    if not gw:
        _emit(issues, "no_default_gateway", "warning", "No default gateway reported.", host)


def _check_selinux(facts: Dict[str, Any], issues: List[Dict[str, str]], host: str = None):
    af = facts.get("ansible_facts", facts)
    se = af.get("selinux") or af.get("ansible_selinux")
    if isinstance(se, dict):
        status = (se.get("status") or "").lower()
        mode = (se.get("mode") or "").lower()
        if status == "enabled" and mode != "enforcing":
            _emit(issues, "selinux_not_enforcing", "warning",
                  f"SELinux status is enabled but mode is '{mode}'.", host)


def _check_kernel(facts: Dict[str, Any], issues: List[Dict[str, str]], host: str = None):
    # Flag obviously ancient kernels (< 4.x) as informational (tweak as needed)
    af = facts.get("ansible_facts", facts)
    kernel = af.get("kernel") or af.get("ansible_kernel")
    if kernel:
        try:
            major = int(str(kernel).split(".", 1)[0])
            if major < 4:
                _emit(issues, "old_kernel_major", "info",
                      f"Kernel '{kernel}' is very old; consider upgrades.", host)
        except Exception:
            pass


def analyze_facts(facts: dict) -> List[Dict[str, str]]:
    """
    Accepts either:
      - a single host's facts dict (as returned in ansible_facts), or
      - a mapping: {hostname: facts_dict}

    Returns: list of {"check_name","severity","message"} entries.
    """
    issues: List[Dict[str, str]] = []

    def run_all(f: Dict[str, Any], host: str = None):
        _check_load(f, issues, host)
        _check_memory(f, issues, host)
        _check_disks(f, issues, host)
        _check_network(f, issues, host)
        _check_selinux(f, issues, host)
        _check_kernel(f, issues, host)

    # Single host dict
    run_all(facts, None)
    return issues


def map_severtity_to_int(sev: str) -> int:
    sev = sev.lower()
    if sev == "critical":
        return 3
    elif sev == "warning":
        return 2
    elif sev == "low":
        return 1
    else:
        return 0


def add_host_fact_finding(host_id: str, host_name: str, check_name: str, severity: str, details: dict, message: str):

    findings_collection = get_mongo_collection("findings", "findings")
    finding = {
        "resource_type": "host",
        "resource_id": host_id,
        "resource_name": host_name,
        "check_name": check_name,
        "severity": map_severtity_to_int(severity),
        "details": details,
        "message": message,
        "timestamp": int(time.time()),
    }
    findings_collection.update_one(
        {
            "resource_type": "host",
            "resource_id": host_id,
            "check_name": check_name,
        },
        {
            "$set": finding,
            "$setOnInsert": {"first_seen": int(time.time())},
        },
        upsert=True,
    )


if __name__ == "__main__":

    host_collection = get_mongo_collection("inventory", "host")
    hosts = host_collection.find({"properties.monitoring_enabled": True})

    ansible_hosts_content = "[all]\n"
    ansible_hosts_dict = {}
    for host in hosts:
        print(host)
        props = host.get("properties", {})
        ssh_enabled = props.get("ssh_enabled", False)
        if not ssh_enabled:
            continue

        hostname = props.get("hostname")
        if not hostname:
            print("Skipping host with no hostname")
            continue

        ip_address = props.get("ip_address", props.get("public_ip"))
        ssh_hostname = props.get("ssh_hostname", hostname)
        ssh_user = props.get("ssh_user", "")
        ssh_port = props.get("ssh_port", "22")
        ssh_key_path = props.get("ssh_key_path", "")
        python_path = props.get("pythonPath", "/usr/bin/python3")
        # ansible_become_method = props.get("ansible_become_method", "sudo")
        ansible_become_user = props.get("ansible_become_user", "root")
        ansible_become_password = props.get("ansible_become_password", "")
        ansible_become = props.get("ansible_become", "false")

        ansible_hosts_content += f"{hostname} ansible_connection=ssh ansible_host={ssh_hostname} ansible_user={ssh_user} ansible_ssh_private_key_file={ssh_key_path} ansible_port={ssh_port} ansible_become={ansible_become} ansible_become_user={ansible_become_user} ansible_python_interpreter={python_path} \n"

        ansible_hosts_dict[hostname] = {
            "ansible_connection": "ssh",
            "ansible_host": ssh_hostname,
            "ansible_user": ssh_user,
            "ansible_ssh_private_key_file": ssh_key_path,
            "ansible_port": ssh_port,
            "ansible_python_interpreter": python_path,
            "ansible_become": ansible_become,
            "ansible_become_user": ansible_become_user,
            "ansible_become_password": ansible_become_password,
        }

    print(ansible_hosts_content)
    print(ansible_hosts_dict)

    with open(f"{DATA_DIR}/ansible_hosts", "w") as f:
        f.write(ansible_hosts_content)

    with open(f"{DATA_DIR}/ansible_hosts.json", "w") as f:
        json.dump(ansible_hosts_dict, f)

    privdata_dir = f"{DATA_DIR}/privdir"
    os.makedirs(privdata_dir, exist_ok=True)
    # copy playbook from resources to privdata_dir/playbooks
    os.makedirs(f"{privdata_dir}/playbooks", exist_ok=True)
    shutil.copyfile(f"{RESOURCES_DIR}/playbooks/facts-all.yml", f"{privdata_dir}/playbooks/facts-all.yml")
    shutil.copyfile(f"{RESOURCES_DIR}/playbooks/facts-min.yml", f"{privdata_dir}/playbooks/facts-min.yml")
    os.makedirs(f"{privdata_dir}/data/ansible_cache", exist_ok=True)

    subset = "all"  # "all" or "min"
    r = ansible_runner.run(
        private_data_dir=privdata_dir,
        inventory={'all': {'hosts': ansible_hosts_dict}},
        playbook=f"playbooks/facts-{subset}.yml",
        extravars={"target": "all"},
        envvars={"ANSIBLE_GATHERING": "smart", "ANSIBLE_GATHER_TIMEOUT": "10", "ANSIBLE_CACHE_PLUGIN": "jsonfile",
                 "ANSIBLE_CACHE_PLUGIN_CONNECTION": "data/ansible_cache"},
    )

    print("status:", r.status, "rc:", r.rc)

    # Extract facts from the event stream (works for both gather_facts and setup)
    facts_by_host = {}
    for ev in r.events:
        if ev.get("event") == "runner_on_ok":
            task = ev.get("event_data", {}).get("task", "")
            # Matches either the implicit "Gathering Facts" task or an explicit setup task
            if task in ("Gathering Facts", "Gather facts", "setup", "ansible.builtin.setup"):
                res = ev["event_data"].get("res", {})
                af = res.get("ansible_facts")
                if af:
                    host = ev["event_data"]["host"]
                    facts_by_host[host] = af


    # Analyze facts and create findings
    for host, af in facts_by_host.items():
        issues = analyze_facts(af)
        print(f"Host: {host}, Issues found: {len(issues)}")
        for issue in issues:
            print(f"  - [{issue['severity'].upper()}] {issue['check_name']}: {issue['message']}")
            add_host_fact_finding(
                host_id=host,
                host_name=host,
                check_name=issue['check_name'],
                severity=issue['severity'],
                details={"message": issue['message']},
                message=issue['message']
            )

    # Save facts to JSON file
    with open(f"{DATA_DIR}/facts_by_host_{subset}.json", "w") as f:
        json.dump(facts_by_host, f, indent=2)

    # # save facts to MongoDB
    # facts_collection = get_mongo_collection("facts", "host_facts")
    # for host, af in facts_by_host.items():
    #     facts_collection.update_one(
    #         {"hostname": host},
    #         {"$set": {f"facts_{subset}": af}},
    #         upsert=True
    #     )

    # update host documents with the gathered facts
    host_collection = get_mongo_collection("inventory", "host")
    for host, af in facts_by_host.items():
        host_collection.update_one(
            {"properties.hostname": host},
            {"$set": {f"ansible_facts_{subset}": af}},
            upsert=False
        )
