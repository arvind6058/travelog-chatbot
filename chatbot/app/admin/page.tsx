import { redirect } from "next/navigation";
import { ADMIN_LOGIN_URL } from "@/lib/env";

export default function CustomerAdminEntryPage() {
  redirect(ADMIN_LOGIN_URL);
}
