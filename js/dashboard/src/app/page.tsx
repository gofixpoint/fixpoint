import { Metadata } from "next";
import { getUserOrRedirect } from "@propelauth/nextjs/server/app-router";

import { MainContent } from "@/components/layout/main-content";
import HumanInTheLoop from "@/components/human/human-in-the-loop";

export const metadata: Metadata = {
  title: "Human in the Loop",
  description: "Dashboard page for interacting with human in the loop",
};

export default async function HumanInTheLoopPage() {
  const user = await getUserOrRedirect();
  if (!user) {
    return redirectToLogin();
  }

  return (
    <MainContent title="Human in the Loop">
      <HumanInTheLoop />
    </MainContent>
  );
}

function redirectToLogin() {
  return {
    redirect: {
      destination: "/api/auth/login",
      permanent: false,
    },
  };
}
