import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
const buttonVariants = cva('inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/60', { variants: { variant: { default: 'bg-cyan-300 text-slate-950 hover:bg-cyan-200 shadow-[0_0_24px_#54e3e633]', secondary: 'bg-white/[.07] text-slate-200 hover:bg-white/[.12] border border-white/[.08]', ghost: 'text-slate-400 hover:text-white hover:bg-white/[.07]', outline: 'border border-white/10 bg-transparent text-slate-200 hover:bg-white/[.06]' }, size: { default: 'h-10 px-4 py-2', sm: 'h-9 px-3 rounded-lg', icon: 'h-10 w-10' } }, defaultVariants: { variant: 'default', size: 'default' } })
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> { asChild?: boolean }
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant, size, asChild = false, ...props }, ref) => { const Comp = asChild ? Slot : 'button'; return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} /> })
Button.displayName = 'Button'
export { Button, buttonVariants }
