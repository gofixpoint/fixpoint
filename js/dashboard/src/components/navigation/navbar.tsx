"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { LucideIcon, UserRound } from "lucide-react";

import { cn } from "@/lib/utils";

const ICON_SIZE = 30;

export default function Navbar() {
  // TODO: Change color of favicon when hovered on.
  // TODO: Add active state depending on which component is selected
  return (
    <nav
      className={cn(
        "flex flex-col items-center space-y-4 py-4 px-6 h-full gap-5 border-r-2 border-accent min-w-max",
        "bg-card",
      )}
    >
      <Link href="/" className={"flex flex-col items-center"}>
        <Image
          src="/favicon.ico"
          alt="Logo"
          width={ICON_SIZE}
          height={ICON_SIZE}
        />
        Fixpoint
      </Link>
      <NavButton Icon={UserRound} text="Human in the Loop" href="/" />
    </nav>
  );
}

interface NavButtonProps {
  Icon: LucideIcon;
  text: string;
  href: string;
}

function NavButton(props: NavButtonProps): React.JSX.Element {
  const { Icon, text, href } = props;
  const [isHovered, setIsHovered] = useState(false);

  const defaultColor = "white";
  const selectedColor = "#0284c7";
  const focusColorClass = "text-sky-600";
  const linkSelectedClass = focusColorClass;
  const centerLink = `hover:${focusColorClass} flex flex-col items-center`;

  const currentPathname = usePathname();
  const isSelected = currentPathname === href;
  const isHoveredOrSelected = isSelected || isHovered;

  return (
    <Link
      href={href}
      className={cn(centerLink, isHoveredOrSelected ? linkSelectedClass : null)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <Icon
        size={ICON_SIZE}
        color={isHoveredOrSelected ? selectedColor : defaultColor}
        strokeWidth={1}
      />
      {text}
    </Link>
  );
}
