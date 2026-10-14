import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Route protection for the admin console.
 *
 * NOTE: this middleware is a **UX convenience only, not the security boundary**.
 * It can only observe that a session cookie *exists* — it cannot validate the
 * signature, the expiry or the role claim, and a client can forge a cookie.
 * The FastAPI backend enforces `require_admin` (valid signature + admin role +
 * active account) on every `/api/v1/admin/*` route and on the admin realtime
 * socket; this file only saves an obviously signed-out visitor a wasted render.
 */

const ADMIN_COOKIE_NAME = "travelogix_admin_token";
const LOGIN_PATH = "/admin/login";

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  // Everything under /admin except the login screen itself requires a session.
  const isAdminRoute = pathname === "/admin" || pathname.startsWith("/admin/");
  const isLoginRoute = pathname === LOGIN_PATH || pathname.startsWith(`${LOGIN_PATH}/`);

  if (!isAdminRoute || isLoginRoute) {
    return NextResponse.next();
  }

  const token = request.cookies.get(ADMIN_COOKIE_NAME)?.value;
  if (token) {
    return NextResponse.next();
  }

  const next = encodeURIComponent(`${pathname}${search}`);
  const loginUrl = new URL(`${LOGIN_PATH}?next=${next}`, request.url);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  /**
   * Only /admin routes need guarding; skipping everything else keeps static
   * assets and Next.js internals out of the middleware entirely.
   */
  matcher: ["/admin", "/admin/((?!_next|.*\\.[^/]+$).*)"],
};
