import * as React from 'react'
import {ChevronsUpDown, Plus} from 'lucide-react'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuShortcut,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    useSidebar,
} from '@/components/ui/sidebar'
import {useApi} from "@/context/api-context.tsx";
import AppIcon from "@/components/app-icon.tsx";

type EnvironmentSwitcherProps = {
    environments: {
        name: string
        logo: React.ElementType
        plan: string
    }[]
}

export function EnvironmentSwitcher({environments}: EnvironmentSwitcherProps) {
    const {isMobile} = useSidebar()
    const {apiBaseUrl} = useApi()
    const [activeEnv, setActiveEnv] = React.useState(environments[0])

    return (
        <SidebarMenu>
            <SidebarMenuItem>
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <SidebarMenuButton
                            size='lg'
                            className='data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground'
                        >
                            {/*<div*/}
                            {/*    className='bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg'>*/}
                            {/*    <activeEnv.logo className='size-4'/>*/}
                            {/*</div>*/}
                            <div
                                className="bg-sidebar-accent text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                                <AppIcon icon={"satellite"} className="size-4"/>
                            </div>
                            <div className='grid flex-1 text-start text-sm leading-tight'>
                <span className='truncate font-semibold'>
                  mission control
                </span>
                                <span className='truncate text-xs'>{activeEnv.name}</span>
                            </div>
                            <ChevronsUpDown className='ms-auto'/>
                        </SidebarMenuButton>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                        className='w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg'
                        align='start'
                        side={isMobile ? 'bottom' : 'right'}
                        sideOffset={4}
                    >
                        <DropdownMenuLabel className='text-muted-foreground text-xs'>
                            Environments
                        </DropdownMenuLabel>
                        {environments.map((env, index) => (
                            <DropdownMenuItem
                                key={env.name}
                                onClick={() => setActiveEnv(env)}
                                className='gap-2 p-2'
                            >
                                <div className='flex size-6 items-center justify-center rounded-sm border'>
                                    <env.logo className='size-4 shrink-0'/>
                                </div>
                                {env.name}
                                <DropdownMenuShortcut>⌘{index + 1}</DropdownMenuShortcut>
                            </DropdownMenuItem>
                        ))}
                        {/*<DropdownMenuSeparator />*/}
                        {/*<DropdownMenuItem className='gap-2 p-2'>
              <div className='bg-background flex size-6 items-center justify-center rounded-md border'>
                <Plus className='size-4' />
              </div>
              <div className='text-muted-foreground font-medium'>Add team</div>
            </DropdownMenuItem>*/}
                    </DropdownMenuContent>
                </DropdownMenu>
            </SidebarMenuItem>
        </SidebarMenu>
    )
}
