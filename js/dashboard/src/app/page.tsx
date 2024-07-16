import { Metadata } from "next";

import { MainContent } from "@/components/layout/main-content";

export const metadata: Metadata = {
  title: "Human in the Loop",
  description: "Dashboard page for interacting with human in the loop",
};

export default async function HumanInTheLoopPage() {
  return (
    <MainContent title="Human in the Loop">
      <div>Swap with actual component</div>
    </MainContent>
  );
}
