import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Route protection for the customer area.
 *
 * NOTE: this middleware is a **UX convenience only, not the security boundary**.
 * It can only observe that a session cookie *exists* — it cannot validate the
 * signature, the expiry or the account status, and cookies can be forged by the
 * client. The FastAPI backend enforces authentication and ownership on every
 * customer endpoint; this file merely avoids rendering a broken shell for
 * visitors who are obviously signed out.
 */

const CUSTOMER_COOKIE_NAME = "travelogix_customer_session";

/**
 * Protected customer routes (everything rendered by `app/(customer)`).
 * `/`, `/login` and `/register` stay public.
 */
const PROTECTED_PREFIXES: string[] = [
  "/ai-assistant",
  "/shipments",
  "/logistics",
  "/profile",
  "/flights",
  "/hotels",
  "/trains",
  "/buses",
  "/admin",
];

const PUBLIC_PREFIXES: string[] = ["/login", "/register"];

function isProtected(pathname: string): boolean {
  if (PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return false;
  }
  return PROTECTED_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

const LOGIN_PATH = "/login";

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  if (!isProtected(pathname)) {
    return NextResponse.next();
  }

  const sessionCookie = request.cookies.get(CUSTOMER_COOKIE_NAME)?.value;
  if (sessionCookie) {
    return NextResponse.next();
  }

  const next = encodeURIComponent(`${pathname}${search}`);
  const loginUrl = new URL(`${LOGIN_PATH}?next=${next}`, request.url);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  /**
   * Skip Next.js internals, static assets and files with an extension so the
   * middleware never intercepts images, fonts or RSC payload fetches.
   */
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.[^/]+$).*)"],
};
