type DataTableColumn = {
  key: string;
  label: string;
};

type DataTableRow = {
  id: string;
  [key: string]: React.ReactNode;
};

type DataTableProps = {
  columns: DataTableColumn[];
  rows: DataTableRow[];
};

export function DataTable({ columns, rows }: DataTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="border-b border-border px-5 py-3 text-xs font-semibold uppercase tracking-normal text-ink-subtle">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="transition hover:bg-surface/70">
              {columns.map((column) => (
                <td key={column.key} className="border-b border-border px-5 py-4 align-middle text-ink-muted">
                  {row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
