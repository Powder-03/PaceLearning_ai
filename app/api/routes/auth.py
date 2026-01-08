"""
Authentication Routes.

API endpoints for user registration, login, email verification, 
password reset, and profile management.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.user_service import user_service, UserService
from app.services.email_service import email_service, EmailService
from app.core.auth import (
    create_access_token,
    get_current_user,
    require_verified_user,
    AuthUser,
)
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    MessageResponse,
    ChangePasswordRequest,
    UpdateProfileRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_user_service() -> UserService:
    """Get UserService instance."""
    return user_service


def get_email_service() -> EmailService:
    """Get EmailService instance."""
    return email_service


# =============================================================================
# REGISTRATION & LOGIN
# =============================================================================


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    request: RegisterRequest,
    service: UserService = Depends(get_user_service),
    email_svc: EmailService = Depends(get_email_service),
):
    """
    Register a new user.
    
    Creates a new user account and sends a verification email.
    The user will need to verify their email before accessing protected resources.
    
    **Request Body:**
    - `email`: Valid email address
    - `password`: Password (min 6 characters)
    - `name`: Optional display name
    """
    try:
        # Create user
        user = await service.create_user(
            email=request.email,
            password=request.password,
            name=request.name,
        )
        
        # Create verification token and send email
        verification_token = await service.create_verification_token(user["user_id"])
        await email_svc.send_verification_email(
            to_email=user["email"],
            user_name=user.get("name"),
            verification_token=verification_token,
        )
        
        # Create access token (user is not verified yet)
        token = create_access_token(
            user_id=user["user_id"],
            email=user["email"],
            name=user.get("name"),
            is_verified=False,
        )
        
        return AuthResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                user_id=user["user_id"],
                email=user["email"],
                name=user.get("name"),
                is_verified=False,
                created_at=user.get("created_at"),
            ),
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    service: UserService = Depends(get_user_service),
):
    """
    Login with email and password.
    
    Returns an access token on successful authentication.
    Note: Unverified users can log in but will have limited access.
    """
    user = await service.authenticate(
        email=request.email,
        password=request.password,
    )
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Create access token
    token = create_access_token(
        user_id=user["user_id"],
        email=user["email"],
        name=user.get("name"),
        is_verified=user.get("is_verified", False),
    )
    
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            name=user.get("name"),
            is_verified=user.get("is_verified", False),
            created_at=user.get("created_at"),
        ),
    )


# =============================================================================
# EMAIL VERIFICATION
# =============================================================================


@router.get("/verify-email", response_model=AuthResponse)
async def verify_email_get(
    token: str = Query(..., description="Verification token from email"),
    service: UserService = Depends(get_user_service),
    email_svc: EmailService = Depends(get_email_service),
):
    """
    Verify email address via GET request (for email link clicks).
    
    When users click the verification link in their email, the browser
    makes a GET request. This endpoint verifies the email and returns
    a new JWT token with is_verified=true.
    
    Returns:
    - AuthResponse with new JWT token on success
    - 400 error if token is invalid or expired
    """
    user = await service.verify_email(token)
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )
    
    # Send welcome email
    await email_svc.send_welcome_email(
        to_email=user["email"],
        user_name=user.get("name"),
    )
    
    # Create new token with verified status
    new_token = create_access_token(
        user_id=user["user_id"],
        email=user["email"],
        name=user.get("name"),
        is_verified=True,
    )
    
    return AuthResponse(
        access_token=new_token,
        token_type="bearer",
        user=UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            name=user.get("name"),
            is_verified=True,
            created_at=user.get("created_at"),
        ),
    )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    request: ResendVerificationRequest,
    service: UserService = Depends(get_user_service),
    email_svc: EmailService = Depends(get_email_service),
):
    """
    Resend verification email.
    
    Use this if the original verification email was not received.
    """
    user = await service.get_user_by_email(request.email)
    
    if not user:
        # Don't reveal if email exists
        return MessageResponse(
            message="If an account exists with this email, a verification link has been sent."
        )
    
    if user.get("is_verified"):
        raise HTTPException(
            status_code=400,
            detail="Email is already verified"
        )
    
    # Create new verification token and send email
    verification_token = await service.create_verification_token(user["user_id"])
    await email_svc.send_verification_email(
        to_email=user["email"],
        user_name=user.get("name"),
        verification_token=verification_token,
    )
    
    return MessageResponse(
        message="If an account exists with this email, a verification link has been sent."
    )


# =============================================================================
# PASSWORD RESET
# =============================================================================


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    service: UserService = Depends(get_user_service),
    email_svc: EmailService = Depends(get_email_service),
):
    """
    Request a password reset email.
    
    Sends a password reset link to the provided email if it exists.
    """
    user = await service.get_user_by_email(request.email)
    
    if user:
        reset_token = await service.create_password_reset_token(request.email)
        if reset_token:
            await email_svc.send_password_reset_email(
                to_email=user["email"],
                user_name=user.get("name"),
                reset_token=reset_token,
            )
    
    # Always return success to prevent email enumeration
    return MessageResponse(
        message="If an account exists with this email, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    service: UserService = Depends(get_user_service),
):
    """
    Reset password with token.
    
    The token is sent via email from the forgot-password endpoint.
    """
    user = await service.reset_password(
        token=request.token,
        new_password=request.new_password,
    )
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    
    return MessageResponse(message="Password reset successfully. You can now log in.")


# =============================================================================
# PROFILE MANAGEMENT
# =============================================================================


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: AuthUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """
    Get current user's profile.
    
    Requires authentication (verified or unverified).
    """
    user = await service.get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user.get("name"),
        is_verified=user.get("is_verified", False),
        created_at=user.get("created_at"),
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: AuthUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """
    Update current user's profile.
    
    Allows updating name and other profile fields.
    """
    try:
        updated_user = await service.update_user(
            user_id=current_user.user_id,
            name=request.name,
        )
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            user_id=updated_user["user_id"],
            email=updated_user["email"],
            name=updated_user.get("name"),
            is_verified=updated_user.get("is_verified", False),
            created_at=updated_user.get("created_at"),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Profile update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: AuthUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """
    Change the current user's password.
    
    Requires the current password for verification.
    """
    try:
        success = await service.change_password(
            user_id=current_user.user_id,
            current_password=request.current_password,
            new_password=request.new_password,
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect"
            )
        
        return MessageResponse(message="Password changed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Password change error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change password")


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    current_user: AuthUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """
    Refresh the access token.
    
    Returns a new access token with extended expiry.
    Requires a valid (non-expired) current token.
    """
    # Verify user still exists in database
    user = await service.get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create new access token
    new_token = create_access_token(
        user_id=user["user_id"],
        email=user["email"],
        name=user.get("name"),
        is_verified=user.get("is_verified", False),
    )
    
    return AuthResponse(
        access_token=new_token,
        token_type="bearer",
        user=UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            name=user.get("name"),
            is_verified=user.get("is_verified", False),
            created_at=user.get("created_at"),
        ),
    )


@router.post("/verify-token", response_model=UserResponse)
async def verify_token_endpoint(
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Verify if the current token is valid.
    
    Returns user info if token is valid, 401 otherwise.
    Useful for frontend to check authentication status.
    """
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        name=current_user.name,
        is_verified=current_user.is_verified,
        created_at=None,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Logout current user.
    
    Note: Since we use stateless JWT, this is just a confirmation.
    The client should discard the token.
    """
    logger.info(f"User {current_user.user_id} logged out")
    return MessageResponse(message="Successfully logged out")


@router.delete("/me", response_model=MessageResponse)
async def delete_account(
    current_user: AuthUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """
    Delete the current user's account.
    
    This action is irreversible. All user data will be deleted.
    """
    try:
        deleted = await service.delete_user(current_user.user_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")
        
        return MessageResponse(message="Account deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Account deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete account")
