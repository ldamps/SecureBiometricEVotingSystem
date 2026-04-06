import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import {
  clearAuthSession,
  hasValidOfficialSession,
} from "../services/api-client.service";

/**
 * Requires a valid official access token for all nested /official/* routes.
 * Public sibling route: /official/landing (not wrapped by this guard).
 */
const OfficialAuthGuard: React.FC = () => {
  if (!hasValidOfficialSession()) {
    clearAuthSession();
    return <Navigate to="/official/landing" replace />;
  }
  return <Outlet />;
};

export default OfficialAuthGuard;
