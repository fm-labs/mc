// Subsets of the Docker Engine API responses passed through by the backend
// (docker SDK `client.info()`, `client.df()` and `.attrs` of containers/images/volumes).

export type DockerInfo = {
    Name?: string
    ServerVersion?: string
    OperatingSystem?: string
    OSType?: string
    Architecture?: string
    KernelVersion?: string
    NCPU?: number
    MemTotal?: number
    Driver?: string
    CgroupVersion?: string
    DockerRootDir?: string
    Containers?: number
    ContainersRunning?: number
    ContainersPaused?: number
    ContainersStopped?: number
    Images?: number
    Swarm?: { LocalNodeState?: string }
    Warnings?: string[] | null
}

export type DfImage = {
    Id: string
    RepoTags?: string[] | null
    Created?: number // unix seconds
    Size?: number
    SharedSize?: number
    Containers?: number
}

export type DfContainer = {
    Id: string
    Names?: string[]
    Image?: string
    ImageID?: string
    State?: string
    SizeRw?: number
    SizeRootFs?: number
}

export type DfVolume = {
    Name: string
    UsageData?: { Size?: number, RefCount?: number } | null
}

export type DfBuildCache = {
    ID: string
    Size?: number
    InUse?: boolean
    Shared?: boolean
}

export type DockerDf = {
    LayersSize?: number
    Images?: DfImage[] | null
    Containers?: DfContainer[] | null
    Volumes?: DfVolume[] | null
    BuildCache?: DfBuildCache[] | null
}

export type PortBinding = { HostIp?: string, HostPort?: string }

// `docker inspect <container>`
export type ContainerAttrs = {
    Id: string
    Name?: string // "/name"
    Created?: string
    Image?: string // sha256 id
    RestartCount?: number
    State?: {
        Status?: string
        Running?: boolean
        Paused?: boolean
        Restarting?: boolean
        OOMKilled?: boolean
        ExitCode?: number
        StartedAt?: string
        FinishedAt?: string
        Health?: { Status?: string, FailingStreak?: number } | null
    }
    Config?: {
        Image?: string
        Labels?: Record<string, string> | null
    }
    HostConfig?: {
        RestartPolicy?: { Name?: string, MaximumRetryCount?: number }
        Memory?: number
        NanoCpus?: number
        CpuQuota?: number
        CpuShares?: number
        PortBindings?: Record<string, PortBinding[] | null> | null
    }
    Mounts?: { Type?: string, Name?: string, Source?: string, Destination?: string }[] | null
}

// `docker image inspect <image>`
export type ImageAttrs = {
    Id: string
    RepoTags?: string[] | null
    Created?: string // ISO date
    Size?: number
}
