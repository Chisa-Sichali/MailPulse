"use client";

import { useState } from "react";
import { Eye, EyeOff, Loader, Lock, Mail } from "lucide-react";
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
  const [showPassword, setShowPassword] = useState(false);

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
        <div className="relative">
          <Mail className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
          <Input
            className="px-9"
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="Email Address"
            onChange={(e) =>
              setFormData({ ...formData, email: e.target.value })
            }
          />
        </div>
      </Field>
      <Field>
        <FieldLabel htmlFor="password">Password</FieldLabel>
        <div className="relative">
          <Lock className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
          <Input
            className="px-9 pr-10"
            id="password"
            name="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            placeholder="Password"
            onChange={(e) =>
              setFormData({ ...formData, password: e.target.value })
            }
          />
          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            className="text-muted-foreground hover:text-foreground absolute top-1/2 right-3 -translate-y-1/2 transition-colors focus:outline-none"
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
        </div>
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
