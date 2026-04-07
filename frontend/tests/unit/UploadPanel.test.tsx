import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { UploadPanel } from "../../src/components/UploadPanel";


test("rejects non-pdf files and triggers upload for valid selection", async () => {
  const onUpload = vi.fn().mockResolvedValue(undefined);
  render(<UploadPanel onUpload={onUpload} />);

  const input = screen.getByLabelText(/choose pdfs/i, { selector: "input" });
  const invalidFile = new File(["hello"], "notes.txt", { type: "text/plain" });
  fireEvent.change(input, { target: { files: [invalidFile] } });

  expect(screen.getByText(/only pdf files/i)).toBeInTheDocument();

  const validFile = new File(["%PDF"], "report.pdf", { type: "application/pdf" });
  fireEvent.change(input, { target: { files: [validFile] } });
  fireEvent.click(screen.getByRole("button", { name: /queue files/i }));

  await waitFor(() => expect(onUpload).toHaveBeenCalledWith([validFile]));

});

