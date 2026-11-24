import { roleLabel, roleUser } from "@/shared/i18n/es";
import { fetchCaseToday } from "@/shared/lib/case-date";
import { formatDate } from "@/shared/lib/format";
import { getSession } from "@/shared/lib/session";

function initials(name: string) {
  return name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("");
}

/** Who is signed in (dynamic: render inside <Suspense>). */
export async function SessionSummary() {
  const session = await getSession();
  if (!session) return null;
  const user = roleUser[session.role];
  const today = await fetchCaseToday();
  return (
    <div className="flex items-center gap-3" aria-label={`Sesión de ${user.name}, ${roleLabel[session.role]}`}>
      <span className="text-label-sm md:hidden">{user.name}</span>
      <span className="hidden text-right leading-tight md:block">
        <span className="block text-label-sm">{user.name}</span>
        <span className="block text-caption text-muted-foreground">
          {roleLabel[session.role]} · {formatDate(today)}
        </span>
      </span>
      <span
        aria-hidden
        title={`${user.name} — ${user.title}`}
        className="grid size-9 shrink-0 place-items-center rounded-full bg-primary-soft font-display text-label-sm text-primary-soft-foreground ring-1 ring-primary/20"
      >
        {initials(user.name)}
      </span>
    </div>
  );
}
