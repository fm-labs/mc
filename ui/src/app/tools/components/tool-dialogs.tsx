import { ToolDrawer } from "@/app/tools/components/tool-drawer.tsx";
import { useTools } from "@/app/tools/components/tools-provider.tsx";

export function ToolsDialogs() {
  const { open, setOpen, currentTool, commandName, setCurrentTool } = useTools()
  return (
    <>
      {currentTool && (
        <>
          <ToolDrawer
            key={`tool-run`}
            open={open === 'run'}
            onOpenChange={() => {
              setOpen('run')
              setTimeout(() => {
                setCurrentTool(null, null)
              }, 500)
            }}
            tool={currentTool}
            commandName={commandName}
          />
        </>
      )}
    </>
  )
}
