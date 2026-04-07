import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { ChatPanel } from "../../src/components/ChatPanel";


test("renders messages and sends a new prompt", async () => {
  const onSend = vi.fn().mockResolvedValue(undefined);
  render(
    <ChatPanel
      onSend={onSend}
      messages={[
        {
          id: "1",
          role: "assistant",
          content: "Revenue reached 12.3M [1]",
          citations: [
            {
              chunk_id: "c1",
              document_id: "d1",
              document_name: "report.pdf",
              page_number: 3,
              snippet: "Revenue reached 12.3M",
              relevance: 0.92,
            },
          ],
          created_at: new Date().toISOString(),
        },
      ]}
    />,
  );

  expect(screen.getAllByText(/Revenue reached 12.3M/i).length).toBeGreaterThan(0);
  fireEvent.change(screen.getByLabelText(/message input/i), {
    target: { value: "Summarize the trend" },
  });
  fireEvent.click(screen.getByRole("button", { name: /send/i }));

  expect(onSend).toHaveBeenCalledWith("Summarize the trend");
});

