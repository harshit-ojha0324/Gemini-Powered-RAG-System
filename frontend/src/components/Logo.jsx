// A page with one line run through a highlighter: documents, and the evidence
// pulled from them. Mirrors public/favicon.svg.
function Logo({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <rect width="24" height="24" rx="6" fill="var(--green)" />
      <path d="M7.25 5h6.5L17 8.25V18a1 1 0 0 1-1 1H7.25a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z" fill="#fff" />
      <path d="M13.5 5v3.5H17" fill="none" stroke="var(--green)" strokeWidth="1" strokeLinejoin="round" />
      <rect x="8.25" y="11" width="6.75" height="2.25" rx="0.5" fill="var(--marker)" />
      <rect x="8.25" y="14.75" width="4.75" height="1.25" rx="0.5" fill="#b9c7c1" />
    </svg>
  );
}

export default Logo;
