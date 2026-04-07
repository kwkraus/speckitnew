import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { DocumentLibrary } from "../../src/components/DocumentLibrary";


test("renders the table, supports filtering, and confirms deletion", () => {
  const onDelete = vi.fn().mockResolvedValue(undefined);
  const onStatusFilterChange = vi.fn();
  vi.spyOn(window, "confirm").mockReturnValue(true);

  render(
    <DocumentLibrary
      documents={[
        {
          id: "doc-1",
          filename: "report.pdf",
          status: "completed",
          file_size: 1024,
          page_count: 4,
          chunk_count: 12,
          created_at: new Date().toISOString(),
        },
      ]}
      statusFilter="all"
      onStatusFilterChange={onStatusFilterChange}
      onDelete={onDelete}
    />,
  );

  expect(screen.getByText(/report.pdf/i)).toBeInTheDocument();
  fireEvent.change(screen.getByDisplayValue(/all/i), { target: { value: "completed" } });
  expect(onStatusFilterChange).toHaveBeenCalledWith("completed");

  fireEvent.click(screen.getByRole("button", { name: /delete/i }));
  expect(onDelete).toHaveBeenCalledWith("doc-1");
});
