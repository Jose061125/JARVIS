import { z } from "zod";

const powerActionSchema = z.enum(["shutdown", "restart", "sleep", "lock"]);

export function validatePowerAction(action: string): boolean {
  return powerActionSchema.safeParse(action).success;
}
