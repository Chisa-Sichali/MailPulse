"use client";

import { useState } from "react";
import { Loader } from "lucide-react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/toast";
import { Field, FieldLabel } from "@/components/ui/field";
import { useLoginUser } from "@/hooks/auth/useLoginUser";

type FormValues = {
  email: string;
  password: string;
};
export function LoginContainer() {
  const [formData, setFormData] = useState<FormValues>({
    email: "",
    password: "",
  });

  const router = useRouter();
  const { mutate, isPending } = useLoginUser();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    mutate(formData, {
      onSuccess: () => {
        toast.add({
          title: "Login successful",
          description: "Welcome back! redirecting...",
          type: "success",
        });

        router.push("/dashboard");
      },

      onError: (error) => {
        toast.add({
          title: "Login failed",
          description: error.message,
          type: "error",
          timeout: 7000,
        });
      },
    });
  };
  return (
    <form className="mt-5 flex w-full flex-col gap-5" onSubmit={handleSubmit}>
      <Field>
        <FieldLabel htmlFor="email">Email</FieldLabel>
        <Input
          className="px-5"
          name="email"
          type="email"
          autoComplete="email"
          placeholder="Email Address"
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        />
      </Field>
      <Field>
        <FieldLabel htmlFor="password">Password</FieldLabel>
        <Input
          className="px-5"
          name="password"
          type="password"
          autoComplete="current-password"
          placeholder="Password"
          onChange={(e) =>
            setFormData({ ...formData, password: e.target.value })
          }
        />
      </Field>
      <Button
        type="submit"
        disabled={isPending}
        className={`mt-1 h-11 w-full cursor-pointer bg-linear-to-r from-[#6366f1] to-[#8b5cf6] ${isPending ? "opacity-50 cursor-not-allowed" : "hover:opacity-90"} text-white`}
      >
        {isPending ? (
          <Loader className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <span>Login</span>
        )}
      </Button>
    </form>
  );
}
