declare module 'vuedraggable' {
  import { DefineComponent, SlotsType } from 'vue'

  interface DraggableProps<T = any> {
    modelValue?: T[]
    itemKey?: string | ((item: T) => string | number)
    tag?: string
    clone?: (item: T) => T
    move?: (evt: any) => boolean | void
    group?: string | { name: string; pull?: boolean | string; put?: boolean | string[] }
    handle?: string
    disabled?: boolean
    animation?: number
    componentData?: Record<string, any>
  }

  interface DraggableSlots<T = any> {
    item: (props: { element: T; index: number }) => any
    header: () => any
    footer: () => any
  }

  const component: DefineComponent<DraggableProps, {}, {}, {}, {}, {}, {}, {}, string, {}, {}, SlotsType<DraggableSlots>>
  export default component
}
