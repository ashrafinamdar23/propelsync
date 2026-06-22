import Keycloak from "keycloak-js";

const tokenStorageKey = "propelsync.keycloak.tokens";

type StoredTokens = {
  token?: string;
  refreshToken?: string;
  idToken?: string;
};

export const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL,
  realm: import.meta.env.VITE_KEYCLOAK_REALM,
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID
});

let keycloakInitPromise: Promise<boolean> | null = null;

function readStoredTokens(): StoredTokens {
  const raw = window.localStorage.getItem(tokenStorageKey);
  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw) as StoredTokens;
  } catch {
    window.localStorage.removeItem(tokenStorageKey);
    return {};
  }
}

function isJwtUsable(token: string | undefined): boolean {
  if (!token) {
    return false;
  }

  const [, payload] = token.split(".");
  if (!payload) {
    return false;
  }

  try {
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const decoded = JSON.parse(window.atob(normalized)) as { exp?: number };
    return typeof decoded.exp === "number" && decoded.exp * 1000 > Date.now() + 30_000;
  } catch {
    return false;
  }
}

export function saveKeycloakTokens(): void {
  if (!keycloak.token || !keycloak.refreshToken) {
    return;
  }

  window.localStorage.setItem(
    tokenStorageKey,
    JSON.stringify({
      token: keycloak.token,
      refreshToken: keycloak.refreshToken,
      idToken: keycloak.idToken
    })
  );
}

export function clearKeycloakTokens(): void {
  window.localStorage.removeItem(tokenStorageKey);
}

export function initKeycloak(): Promise<boolean> {
  if (!keycloakInitPromise) {
    const storedTokens = readStoredTokens();
    const tokenOptions = isJwtUsable(storedTokens.refreshToken)
      ? {
          token: storedTokens.token,
          refreshToken: storedTokens.refreshToken,
          idToken: storedTokens.idToken
        }
      : {};

    keycloakInitPromise = keycloak.init({
      onLoad: "check-sso",
      pkceMethod: "S256",
      checkLoginIframe: false,
      ...tokenOptions
    }).then((authenticated) => {
      if (authenticated) {
        saveKeycloakTokens();
      } else {
        clearKeycloakTokens();
      }
      return authenticated;
    }).catch((error) => {
      clearKeycloakTokens();
      keycloakInitPromise = null;
      throw error;
    });

    keycloak.onAuthRefreshSuccess = saveKeycloakTokens;
    keycloak.onAuthSuccess = saveKeycloakTokens;
    keycloak.onAuthLogout = clearKeycloakTokens;
    keycloak.onTokenExpired = () => {
      void keycloak.updateToken(30).then(saveKeycloakTokens).catch(clearKeycloakTokens);
    };
  }

  return keycloakInitPromise;
}
