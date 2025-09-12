
from orchestra.interface import ko_playbook_run
#from orchestra.playbooks.wireguard_server import wireguard_server_playbook
#from orchestra.tasks import run_ansible_playbook_task

if __name__ == '__main__':
    print("Kloudia Orchestra")

    #project = sys.argv[1]
    project = "ama-gameserver"
    target = "amatic.grandx.gs155"
    #playbook = "playbooks/gameserver-baseline"
    playbook = "playbooks/gameserver-dockerhost"

    #project = "fmlabs"
    #target = "fmhub.srv04"
    #playbook = "builtin/dockerhost-debian"


    extravars = {"target": target}
    cmdline = "--vault-password-file secrets/gameserver.vault_password --extra-vars @secrets/gameserver.yml"
    result = ko_playbook_run(
        project=project,
        playbook=playbook,
        extravars=extravars,
        #cmdline="--check",
        cmdline=cmdline,
    )
    print(result)

    # task_result = run_ansible_playbook_task.apply_async(
    #     kwargs={
    #         "project": project,
    #         "playbook": playbook,
    #         "extravars": extravars,
    #     }
    # )
    # print(task_result)

    #wireguard_server_playbook(project, target, dryrun=False)