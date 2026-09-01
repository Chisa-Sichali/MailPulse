"use client";

import { Loader } from "lucide-react";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Field, FieldLabel } from "@/components/ui/field";
import { useCreateUser } from "@/hooks/auth/useCreateUser";

type FormValues = {
  username: string;
  email: string;
  password: string;
};

export function SignupContainer() {
  const [formData, setFormData] = useState<FormValues>({
    username: "",
    email: "",
    password: "",
  });

  const router = useRouter();
  const { mutate, isPending } = useCreateUser();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    mutate(formData, {
      onSuccess: () => {
        toast.add({
          title: "Account created",
          description: "Welcome to MailPulse!",
          type: "success",
        });
        router.push("/dashboard");
      },

      onError: (error) => {
        toast.add({
          title: "Signup failed",
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
        <FieldLabel htmlFor="fullName">Full Name</FieldLabel>
        <Input
          className="px-5"
          name="fullName"
          type="text"
          autoComplete="name"
          placeholder="Full Name"
          onChange={(e) =>
            setFormData({ ...formData, username: e.target.value })
          }
        />
      </Field>
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
          autoComplete="new-password"
          placeholder="Password"
          onChange={(e) =>
            setFormData({ ...formData, password: e.target.value })
          }
        />
      </Field>
      <Button
        type="submit"
        disabled={isPending}
        className="mt-1 h-11 w-full cursor-pointer bg-linear-to-r from-[#6366f1] to-[#8b5cf6] text-white hover:opacity-90"
      >
        {isPending ? (
          <Loader className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <span>Create account</span>
        )}
      </Button>
    </form>
  );
}
