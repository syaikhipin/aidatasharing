import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "gradient" | "success"
  size?: "default" | "sm" | "lg" | "xl" | "icon"
  isLoading?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", isLoading = false, children, disabled, ...props }, ref) => {
    return (
      <button
        className={cn(
          // Base styles
          "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 relative overflow-hidden",
          
          // Variant styles
          {
            "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg hover:-translate-y-0.5 focus-visible:ring-blue-500": variant === "default",
            "bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 hover:shadow-lg hover:-translate-y-0.5 focus-visible:ring-blue-500": variant === "gradient",
            "bg-red-600 text-white hover:bg-red-700 hover:shadow-lg hover:-translate-y-0.5 focus-visible:ring-red-500": variant === "destructive",
            "bg-green-600 text-white hover:bg-green-700 hover:shadow-lg hover:-translate-y-0.5 focus-visible:ring-green-500": variant === "success",
            "border-2 border-gray-300 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-400 hover:shadow-md focus-visible:ring-gray-500": variant === "outline",
            "bg-gray-100 text-gray-900 hover:bg-gray-200 hover:shadow-md focus-visible:ring-gray-500": variant === "secondary",
            "hover:bg-gray-100 hover:text-gray-900 focus-visible:ring-gray-500": variant === "ghost",
            "text-blue-600 underline-offset-4 hover:underline focus-visible:ring-blue-500": variant === "link",
          },
          
          // Size styles
          {
            "h-10 px-4 py-2": size === "default",
            "h-8 rounded-md px-3 text-xs": size === "sm",
            "h-12 rounded-lg px-8 text-base": size === "lg",
            "h-14 rounded-xl px-10 text-lg": size === "xl",
            "h-10 w-10": size === "icon",
          },
          className
        )}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          </div>
        )}
        <span className={cn("flex items-center gap-2", isLoading && "opacity-0")}>
          {children}
        </span>
      </button>
    )
  }
)
Button.displayName = "Button"

export { Button }