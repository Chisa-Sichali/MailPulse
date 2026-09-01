import { Mail } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { SignupContainer } from "./SignupContainer";
import { LoginContainer } from "./LoginContainer";

export default function AuthContainer() {
  return (
    <div className="flex min-h-dvh items-center justify-center bg-background px-4 py-8 sm:px-6">
      <div className="flex w-full max-w-md flex-col">
        {/* Brand */}
        <div className="flex items-center justify-center gap-2.5">
          <div className="flex items-center justify-center rounded-lg bg-linear-to-r from-[#6366f1] to-[#8b5cf6] p-2">
            <Mail size={20} className="text-white" />
          </div>

          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Mail<span className="text-[#8b5cf6]">Pulse</span>
          </h1>
        </div>

        {/* Card */}
        <div className="mt-6 w-full rounded-2xl border bg-card p-6 shadow-sm sm:mt-8 sm:p-8">
          <Tabs defaultValue="login" className="w-full">
            <TabsList className="w-full">
              <TabsTrigger value="login">Login</TabsTrigger>
              <TabsTrigger value="signup">Signup</TabsTrigger>
            </TabsList>
            <TabsContent value="login">
              <LoginContainer />
            </TabsContent>
            <TabsContent value="signup">
              <SignupContainer />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
