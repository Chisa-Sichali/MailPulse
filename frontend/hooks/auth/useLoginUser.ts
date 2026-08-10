import { useMutation } from "@tanstack/react-query";
import { authService } from "@/services/auth";
import { LoginRequest, CreateUserResponse } from "@/services/Types";

export const useLoginUser = () => {
  return useMutation<CreateUserResponse, Error, LoginRequest>({
    mutationFn: (request: LoginRequest) => authService.LoginUser(request),
  });
};
