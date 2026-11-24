"use client";

import { ExternalLink, ScanText } from "lucide-react";

import { extractionMethodLabel } from "@/shared/i18n/es";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/primitives/tabs";

interface SourceViewerProps {
  documentId: string;
  documentName: string;
  isEmailBody: boolean;
  extractionMethod: string;
  ocrConfidence: number | null;
  text: string;
  emailBody: string;
}

export function SourceViewer(props: SourceViewerProps) {
  const fileUrl = `/files/documents/${encodeURIComponent(props.documentId)}`;
  const isPdf = props.documentName.toLowerCase().endsWith(".pdf");
  return (
    <Tabs defaultValue="original" className="gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <TabsList>
          <TabsTrigger value="original">Original</TabsTrigger>
          <TabsTrigger value="text">Texto leído</TabsTrigger>
          {!props.isEmailBody ? <TabsTrigger value="email">Correo</TabsTrigger> : null}
        </TabsList>
        <p className="flex items-center gap-1.5 text-caption text-muted-foreground">
          <ScanText aria-hidden className="size-3.5" />
          {extractionMethodLabel[props.extractionMethod] ?? "Formato no reconocido"}
          {props.ocrConfidence !== null ? ` · confianza ${Math.round(props.ocrConfidence)}%` : ""}
        </p>
      </div>
      <TabsContent value="original">
        {isPdf ? (
          <div className="overflow-hidden rounded-xl border bg-muted">
            <iframe title={`Documento original: ${props.documentName}`} src={fileUrl} className="h-[70dvh] w-full" />
            <a
              href={fileUrl}
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-center gap-1.5 border-t bg-card py-2 text-label-sm text-primary"
            >
              <ExternalLink aria-hidden className="size-4" /> Abrir en otra pestaña
            </a>
          </div>
        ) : (
          <pre className="max-h-[70dvh] overflow-auto whitespace-pre-wrap rounded-xl border bg-card p-4 font-sans text-body-sm">
            {props.isEmailBody ? props.emailBody : props.text || "Sin vista previa para este formato."}
          </pre>
        )}
      </TabsContent>
      <TabsContent value="text">
        <pre className="max-h-[70dvh] overflow-auto whitespace-pre-wrap rounded-xl border bg-card p-4 font-mono text-caption">
          {props.text || "No se pudo extraer texto de este documento."}
        </pre>
      </TabsContent>
      {!props.isEmailBody ? (
        <TabsContent value="email">
          <pre className="max-h-[70dvh] overflow-auto whitespace-pre-wrap rounded-xl border bg-card p-4 font-sans text-body-sm">
            {props.emailBody || "El correo no tiene texto."}
          </pre>
        </TabsContent>
      ) : null}
    </Tabs>
  );
}
