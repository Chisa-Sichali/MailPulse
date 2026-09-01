import {useMutation} from "@tanstack/react-query";
import {authService} from "@/services/auth";
import {CreateUserRequest, CreateUserResponse} from "@/services/Types";

export const useCreateUser = () => {
    return useMutation<CreateUserResponse, Error, CreateUserRequest>({
        mutationFn: (request: CreateUserRequest) => authService.CreateUser(request)
    })
}