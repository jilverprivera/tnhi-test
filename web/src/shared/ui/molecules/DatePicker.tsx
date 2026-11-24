"use client";

import { CalendarDays, X } from "lucide-react";
import { useState } from "react";
import { es } from "react-day-picker/locale";

import { cn } from "@/shared/lib/cn";
import { formatDate } from "@/shared/lib/format";
import { Button } from "@/shared/ui/primitives/button";
import { Calendar } from "@/shared/ui/primitives/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/ui/primitives/popover";

const toIso = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const fromIso = (iso: string) => {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
};

interface DatePickerProps {
  id: string;
  /** Submitted with a surrounding <form> as YYYY-MM-DD (hidden input). */
  name?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (iso: string) => void;
  placeholder?: string;
  /** "Today" in the case (not the machine clock). */
  today?: string;
  className?: string;
  "aria-invalid"?: boolean;
}

/** Design-system date field: the calendar is the app's own popover, in Spanish, never the browser's. */
export function DatePicker({
  id,
  name,
  value,
  defaultValue = "",
  onChange,
  placeholder = "Elegir fecha",
  today,
  className,
  "aria-invalid": ariaInvalid,
}: DatePickerProps) {
  const [inner, setInner] = useState(defaultValue);
  const [open, setOpen] = useState(false);
  const current = value ?? inner;
  const set = (iso: string) => {
    if (value === undefined) setInner(iso);
    onChange?.(iso);
  };
  const todayDate = today ? fromIso(today) : new Date();

  return (
    <div className={cn("relative", className)}>
      {name ? <input type="hidden" name={name} value={current} /> : null}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            id={id}
            type="button"
            variant="outline"
            aria-invalid={ariaInvalid}
            className={cn("w-full justify-start gap-2 bg-card font-normal", !current && "text-muted-foreground")}
          >
            <CalendarDays aria-hidden className="size-4 text-muted-foreground" />
            {current ? formatDate(current) : placeholder}
          </Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-auto p-0">
          <Calendar
            mode="single"
            locale={es}
            selected={current ? fromIso(current) : undefined}
            defaultMonth={current ? fromIso(current) : todayDate}
            today={todayDate}
            onSelect={(d) => {
              if (d) set(toIso(d));
              setOpen(false);
            }}
            captionLayout="label" /* month dropdowns would be native <select>s: arrows keep it in the design system */
          />
          <div className="flex justify-between border-t p-2">
            <Button type="button" variant="ghost" size="sm" onClick={() => { set(""); setOpen(false); }}>
              <X aria-hidden /> Borrar
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={() => { set(toIso(todayDate)); setOpen(false); }}>
              Hoy
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
