"use client";

import { useState } from "react";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/primitives/select";

/** Radix needs a non-empty value for every item: this sentinel means "no filter". */
export const ALL_OPTIONS = "ALL";

interface FilterSelectProps {
  id: string;
  /** Field name submitted with the surrounding <form> (Radix renders a hidden native field). */
  name: string;
  label: string;
  allLabel: string;
  options: { value: string; label: string }[];
  defaultValue?: string;
  className?: string;
}

/**
 * Design-system select for filters: the open list is the app's own popover (tokens, focus, motion),
 * never the browser's native dropdown. Works inside plain GET forms.
 */
export function FilterSelect({ id, name, label, allLabel, options, defaultValue, className }: FilterSelectProps) {
  const [value, setValue] = useState(defaultValue || ALL_OPTIONS);
  return (
    <div className={className}>
      <label className="sr-only" htmlFor={id}>
        {label}
      </label>
      <Select name={name} value={value} onValueChange={setValue}>
        <SelectTrigger id={id} aria-label={label}>
          <SelectValue placeholder={allLabel} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_OPTIONS}>{allLabel}</SelectItem>
          {options.map((o) => (
            <SelectItem key={o.value} value={o.value}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
