/** 'auto' when the user asked for reduced motion, otherwise 'smooth'. */
export function scrollBehavior() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
}
