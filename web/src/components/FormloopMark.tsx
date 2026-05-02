import type { ImgHTMLAttributes } from "react";

export function FormloopMark({ alt = "", ...props }: ImgHTMLAttributes<HTMLImageElement>) {
  return <img src="/brand/formloop-mark.png" alt={alt} {...props} />;
}

export function FormloopWordmark({ alt = "Formloop", ...props }: ImgHTMLAttributes<HTMLImageElement>) {
  return <img src="/brand/formloop-wordmark.png" alt={alt} {...props} />;
}
