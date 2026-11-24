import { z } from "zod";

import { ACTIONS, DEPARTMENTS, DOCUMENT_TYPES } from "@/shared/lib/api-types";

export const documentCorrectionSchema = z
  .object({
    documentType: z.enum(DOCUMENT_TYPES),
    department: z.enum(DEPARTMENTS),
    action: z.enum(ACTIONS),
    dueDate: z.string().regex(/^(\d{4}-\d{2}-\d{2})?$/, "Use el formato AAAA-MM-DD"),
    isUrgent: z.boolean(),
    notes: z.string().max(500, "Máximo 500 caracteres"),
  })
  .refine((v) => !((v.action === "FILE" || v.action === "HOLD_FOR_VERIFICATION") && v.department === "NONE"), {
    path: ["department"],
    message: "Para radicar hay que elegir la dependencia.",
  });

export type DocumentCorrectionValues = z.infer<typeof documentCorrectionSchema>;
