import { Link } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { PageHeader } from "@/components/common/PageHeader";

export function ComingSoonPage({ title, description }: { title: string; description: string }) {
  return (
    <div>
      <PageHeader title={title} description={description} />
      <EmptyState
        title="En construcción"
        description="Este módulo se habilita en la próxima etapa del proyecto."
        action={
          <Link to="/dashboard" className="text-sm font-medium text-brand-600 hover:underline">
            Volver al dashboard
          </Link>
        }
      />
    </div>
  );
}