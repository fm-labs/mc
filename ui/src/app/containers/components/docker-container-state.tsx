import { Badge } from "@/components/ui/badge.tsx";
import { IconRefresh, IconSkull } from "@tabler/icons-react";

/**
 * ContainerState
 *
 * {
 *  "State": {
 *    "Dead": false,
 *    "Error": "",
 *    "ExitCode": 0,
 *    "FinishedAt": "0001-01-01T00:00:00Z",
 *    "Health": {
 *      "FailingStreak": 0,
 *      "Log": [
 *        {
 *          "End": "2025-02-06T10:16:45.260954801Z",
 *          "ExitCode": 0,
 *          "Output": "{\n  \"status\": \"OK\",\n  \"version\": \"1.0.0\"\n}\n",
 *          "Start": "2025-02-06T10:16:45.214070801Z"
 *        },
 *        {
 *          "End": "2025-02-06T10:18:15.308925551Z",
 *          "ExitCode": 0,
 *          "Output": "{\n  \"status\": \"OK\",\n  \"version\": \"1.0.0\"\n}\n",
 *          "Start": "2025-02-06T10:18:15.266247676Z"
 *        },
 *        {
 *          "End": "2025-02-06T10:19:45.358283468Z",
 *          "ExitCode": 0,
 *          "Output": "{\n  \"status\": \"OK\",\n  \"version\": \"1.0.0\"\n}\n",
 *          "Start": "2025-02-06T10:19:45.312312551Z"
 *        },
 *        {
 *          "End": "2025-02-06T10:21:15.388904676Z",
 *          "ExitCode": 0,
 *          "Output": "{\n  \"status\": \"OK\",\n  \"version\": \"1.0.0\"\n}\n",
 *          "Start": "2025-02-06T10:21:15.351041051Z"
 *        }
 *      ],
 *      "Status": "healthy"
 *    },
 *    "OOMKilled": false,
 *    "Paused": false,
 *    "Pid": 46427,
 *    "Restarting": false,
 *    "Running": true,
 *    "StartedAt": "2025-02-06T10:15:15.107387634Z",
 *    "Status": "running"
 *  }
 * }
 *
 * @param state
 * @constructor
 */
const ContainerState = ({ state }: { state: any }) => {
    const badgeProps: any = {
        //size: "small",
        variant: "outline",
    };

    let label = state?.Status || "unknown";
    let colorClass = "border-gray-500";
    let containerStateEl;
    switch (state?.Status) {
        case "running":
            colorClass = "border-green-500";
            break;
        case "exited":
            colorClass = "border-red-500";
            label = `${state?.Status} (${state?.ExitCode})`;
            break;
        case "created":
            colorClass = "border-blue-500";
            break;
        case "paused":
            colorClass = "border-yellow-500";
            break;
    }
    containerStateEl = <Badge {...badgeProps} className={`${colorClass}`}>{label}</Badge>;

    let healthStateEl;
    if (state?.Health?.Status) {
        const healthBadgeProps: any = {
            //size: "small",
            variant: "outline",
        };
        let healthLabel = state?.Health?.Status || "unknown";
        let healthColor = "border-gray-500";
        switch (state?.Health?.Status) {
            case "healthy":
                healthColor = "border-green-500";
                break;
            case "unhealthy": {
                const failingStreak = state?.Health?.FailingStreak;
                let healthLabel = `${state?.Health?.Status}`;
                if (failingStreak && failingStreak > 0) {
                    healthLabel += ` (${failingStreak})`;
                }
                healthColor = "border-orange-500";
                break;
            }
        }
        healthStateEl = <Badge {...healthBadgeProps} className={`${healthColor}`}>{healthLabel}</Badge>;
    }

    return (
        <>
            {state?.Restarting && <span title={"Restarting"} className={"animate-spin"}>
                <IconRefresh size={"1em"} /></span>}
            {state?.Dead && <span title={"Dead"}>
                <IconSkull size={"1em"} /></span>}
            {state?.OOMKilled && <span title={"Out-of-Memory Killed"}>
                <IconSkull color={"red"} size={"1em"} /></span>}

            {healthStateEl}
            {containerStateEl}
        </>
    );
};

export default ContainerState;
