import * as React from "react";

export interface SimpleInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

export function Input(props: SimpleInputProps) {
  return (
    <input
      {...props}
      className={`border rounded-md px-3 py-2 w-full ${props.className ?? ""}`}
    />
  );
}
