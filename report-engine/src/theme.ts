import { defineTheme } from "@hyper-elements/react";

/** Shared ChayaLab visual identity for all Hyper Elements roots. */
export const chayaTheme = defineTheme({
  colors: {
    background: "#F3F6FA",
    foreground: "#172033",
    primary: "#087E8B",
    primaryForeground: "#FFFFFF",
    muted: "#64748B",
    border: "#DCE4ED",
  },
  fonts: {
    body: "Inter, Arial, sans-serif",
    heading: "Inter, Arial, sans-serif",
  },
});

export const palette = {
  ink: "#172033",
  muted: "#64748B",
  teal: "#087E8B",
  tealLight: "#E6F4F4",
  paper: "#FFFFFF",
  canvas: "#F3F6FA",
  border: "#DCE4ED",
  violet: "#6755A5",
  violetLight: "#F0EDFA",
};
