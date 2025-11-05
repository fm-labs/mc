import { toast } from 'sonner'

export function showDataToast(
  data: unknown,
  title: string = 'Data:'
) {
    console.log("showDataToast data:", data);
  toast.message(title, {
    description: (
      // w-[340px]
        <pre className='mt-2 w-full overflow-x-auto overflow-y-scroll rounded-md bg-slate-950 p-2 max-h-[300px] max-w-[324px]'>
        <code className='text-white'>{JSON.stringify(data, null, 2)}</code>
      </pre>
    ),
  })
}
