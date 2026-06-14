import { useEffect, useRef, useState } from "react";
import { useOutletContext, useParams } from "react-router-dom";

import { excluirFoto, enviarFotos, listarFotos, type Foto } from "../../api/fotos";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import type { OrgOutlet } from "../../layouts/OrganizerLayout";
import { extractErrorMessage } from "../../lib/errors";
import { toastError, toastSuccess } from "../../lib/toast";

import shared from "./shared.module.css";
import styles from "./OrgFotosPage.module.css";

export const OrgFotosPage = () => {
  const { id } = useParams<{ id: string }>();
  const { evento } = useOutletContext<OrgOutlet>();
  const [fotos, setFotos] = useState<Foto[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [fotoExcluir, setFotoExcluir] = useState<Foto | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    listarFotos(id)
      .then((fs) => {
        if (!cancelled) setFotos(fs);
      })
      .catch((err) => {
        if (!cancelled)
          setError(extractErrorMessage(err, "Falha ao carregar a galeria."));
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const aoSelecionar = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!id || !e.target.files || e.target.files.length === 0) return;
    const files = Array.from(e.target.files);
    setEnviando(true);
    try {
      const novas = await enviarFotos(id, files);
      setFotos((prev) => (prev ? [...novas, ...prev] : novas));
      toastSuccess(
        novas.length === 1 ? "Foto publicada!" : `${novas.length} fotos publicadas!`,
      );
    } catch (err) {
      toastError(err, "Falha ao publicar as fotos.");
    } finally {
      setEnviando(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const confirmarExclusao = async () => {
    if (!fotoExcluir) return;
    await excluirFoto(fotoExcluir.id);
    setFotos((prev) => (prev ? prev.filter((f) => f.id !== fotoExcluir.id) : prev));
    toastSuccess("Foto removida.");
  };

  return (
    <>
      <PageHeader
        breadcrumb={`${evento?.nome ?? "Evento"} / Galeria`}
        title="Galeria de fotos"
        actions={
          <>
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              hidden
              onChange={aoSelecionar}
            />
            <button
              className={shared.btnPrimary}
              onClick={() => inputRef.current?.click()}
              disabled={enviando}
            >
              {enviando ? "Enviando…" : "+ Adicionar fotos"}
            </button>
          </>
        }
      />

      <div className={shared.body}>
        {error && (
          <div
            className={shared.cardPadded}
            style={{ borderColor: "#c8102e", color: "#c8102e", marginBottom: 16 }}
          >
            ⚠ {error}
          </div>
        )}

        <div className={shared.card}>
          {fotos === null ? (
            <div style={{ padding: 24, color: "var(--pt-org-text-dim)" }}>
              Carregando galeria…
            </div>
          ) : fotos.length === 0 ? (
            <EmptyState
              icon="📷"
              title="Nenhuma foto publicada ainda"
              hint="Publique as fotos do evento para que os participantes possam vê-las e baixá-las."
              action={
                <button
                  className={shared.btnPrimary}
                  onClick={() => inputRef.current?.click()}
                  disabled={enviando}
                >
                  + Adicionar fotos
                </button>
              }
            />
          ) : (
            <div className={styles.grid}>
              {fotos.map((f) => (
                <div key={f.id} className={styles.item}>
                  <img
                    className={styles.img}
                    src={f.url_thumbnail}
                    alt="Foto do evento"
                    loading="lazy"
                  />
                  <button
                    type="button"
                    className={styles.delete}
                    onClick={() => setFotoExcluir(f)}
                    title="Remover foto"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={fotoExcluir !== null}
        title="Remover foto"
        message="A foto será removida da galeria do evento. Esta ação não pode ser desfeita."
        confirmLabel="Remover"
        cancelLabel="Voltar"
        danger
        onConfirm={confirmarExclusao}
        onClose={() => setFotoExcluir(null)}
      />
    </>
  );
};
