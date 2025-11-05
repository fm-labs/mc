
/**
 *     "Ports": {
 *       "5000/tcp": [
 *         {
 *           "HostIp": "0.0.0.0",
 *           "HostPort": "5000"
 *         }
 *       ]
 *     },data?.NetworkSettings?.Ports
 * @param ports
 * @constructor
 */
const DockerContainerPorts = ({ ports }: { ports: any }) => {
  //console.log('ContainerPorts', ports)

  if (!ports) {
    return <div>-</div>
  }

  return (
    <div className={"flex flex-row space-x-1"}>
      {Object.keys(ports).map((port) => {
        let hostIp = window.location.hostname
        let hostPort = port

        const portData = ports[port]
        if (portData && portData[0]) {
          hostIp = portData[0].HostIp || hostIp
          hostPort = portData[0].HostPort || port
        }

        let hostSchema = 'http'
        if (hostPort === '443') {
          hostSchema = 'https'
        }

        const url = `${hostSchema}://${hostIp}:${hostPort}`
        return (
          <div key={port}>
            <a href={url} target={'_blank'} rel='noreferrer'>{`${hostPort}->${port}`}</a>
          </div>
        )
      })}
    </div>
  )
}

export default DockerContainerPorts
