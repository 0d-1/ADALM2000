"""
ADALM2000 Laboratory - AI Signal Generator Module
© 2024-2026 Odin De Baerdemaker - Tous droits réservés

Module de génération de signaux assistée par Intelligence Artificielle.
Utilise l'API Groq (gratuite) pour interpréter des descriptions
en langage naturel et produire des signaux numpy correspondants.
"""
import numpy as np
import math
import json
import re
import traceback
from urllib import request as urllib_request


class AISignalGenerator:
    """Générateur de signaux piloté par IA via l'API Groq (gratuite)."""

    SYSTEM_PROMPT = """Tu es un assistant expert en traitement du signal intégré dans un oscilloscope ADALM2000.
Ton rôle est de générer des signaux électriques à partir de descriptions en langage naturel.

RÈGLES STRICTES :
1. Tu dois écrire UNIQUEMENT du code Python utilisant numpy (importé comme np) et math.
2. Tu dois déterminer la durée idéale du buffer (`duration` en secondes, max 2.0s) pour que le signal boucle parfaitement (ex: 1 période entière du signal le plus lent).
3. Les variables suivantes seront pré-définies et calculées selon TA `duration` :
   - `sample_rate` : typiquement 400000 Hz
   - `duration` : la durée que tu as choisie
   - `n_samples` : le nombre total d'échantillons (= int(sample_rate * duration))
   - `t` : le vecteur temps = np.linspace(0, duration, n_samples, endpoint=False)
4. Ton code DOIT créer une variable `signal` qui est un np.ndarray de shape (n_samples,).
5. L'amplitude du signal DOIT rester entre -5V et +5V (limites hardware de l'ADALM2000).
6. N'utilise AUCUN import, AUCUN print, AUCUN accès fichier. Seulement numpy et math.
7. Réponds en JSON avec exactement ce format :
{
  "duration": 0.01,
  "explanation": "Explication courte du signal en français",
  "code": "signal = np.sin(2 * np.pi * 1000 * t)  # exemple"
}

EXEMPLES :
- "sinusoïde 1kHz" → duration: 0.001, code: signal = 2.0 * np.sin(2 * np.pi * 1000 * t)
- "carré 500Hz amplitude 3V" → duration: 0.002, code: signal = 1.5 * np.sign(np.sin(2 * np.pi * 500 * t))
- "pulse 1Hz durée 0.35s" → duration: 1.0, code: signal = 2.0 * (t % 1 < 0.35)
- "chirp 100Hz à 10kHz sur 0.5s" → duration: 0.5, code: f=np.linspace(100,10000,n_samples); signal=2.0*np.sin(2*np.pi*np.cumsum(f)/sample_rate)

Rappel : TOUJOURS répondre en JSON valide avec "duration", "explanation" et "code"."""

    def __init__(self):
        self.api_key = ""
        self.conversation_history = []
        self.last_code = ""
        self.last_signal = None

    def set_api_key(self, key: str):
        """Configure la clé API Groq."""
        self.api_key = key.strip()

    def clear_history(self):
        """Réinitialise l'historique de conversation."""
        self.conversation_history = []
        self.last_code = ""
        self.last_signal = None

    def generate_signal(self, user_prompt: str, sample_rate: int = 400000, 
                        current_duration: float = 0.01) -> dict:
        """
        Envoie le prompt à l'API Groq et génère le signal.
        
        Returns:
            dict avec les clés:
            - 'success': bool
            - 'explanation': str (explication de l'IA)
            - 'code': str (code numpy généré)
            - 'signal': np.ndarray ou None
            - 'error': str (message d'erreur si échec)
        """
        if not self.api_key:
            return {
                'success': False,
                'explanation': '',
                'code': '',
                'signal': None,
                'error': "Clé API non configurée. Entrez votre clé API Groq (gratuite) dans les paramètres."
            }

        # Ajouter le message utilisateur à l'historique
        self.conversation_history.append({
            "role": "user",
            "content": user_prompt
        })

        # Construire les messages pour l'API
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        # Contexte technique injecté au début
        context_msg = (
            f"Paramètres matériels : sample_rate={sample_rate} Hz. "
            f"L'utilisateur avait configuré une durée de {current_duration} s, mais tu PEUX et DOIS "
            f"choisir une 'duration' (entre 0.001 et 2.0) pour qu'elle corresponde exactement à 1 période complète "
            f"du signal décrit (ou un multiple), afin que la boucle matérielle soit parfaite."
        )
        messages.append({"role": "system", "content": context_msg})
        messages.extend(self.conversation_history)

        # Appel API Groq
        try:
            response_text = self._call_groq_api(messages)
        except Exception as e:
            # Retirer le message de l'historique en cas d'erreur réseau
            self.conversation_history.pop()
            return {
                'success': False,
                'explanation': '',
                'code': '',
                'signal': None,
                'error': f"Erreur API : {str(e)}"
            }

        # Parser la réponse JSON de l'IA
        try:
            parsed = self._parse_response(response_text)
            explanation = parsed.get('explanation', '')
            code = parsed.get('code', '')
            duration = float(parsed.get('duration', current_duration))
            duration = max(0.0001, min(2.0, duration)) # Sécurité
        except Exception as e:
            self.conversation_history.pop()
            return {
                'success': False,
                'explanation': '',
                'code': '',
                'signal': None,
                'error': f"Erreur de parsing de la réponse IA : {str(e)}\n\nRéponse brute :\n{response_text[:500]}"
            }

        # Exécuter le code en sandbox
        n_samples = int(sample_rate * duration)
        try:
            signal = self._execute_code(code, sample_rate, duration, n_samples)
        except Exception as e:
            # On garde dans l'historique pour que l'IA puisse corriger
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            return {
                'success': False,
                'explanation': explanation,
                'code': code,
                'signal': None,
                'error': f"Erreur d'exécution du code généré :\n{str(e)}"
            }

        # Succès ! Sauvegarder dans l'historique
        self.conversation_history.append({
            "role": "assistant",
            "content": response_text
        })
        self.last_code = code
        self.last_signal = signal

        return {
            'success': True,
            'explanation': explanation,
            'code': code,
            'signal': signal,
            'duration': duration,
            'error': ''
        }

    # Modèles Groq gratuits, par ordre de préférence
    GROQ_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
    ]

    def _call_groq_api(self, messages: list) -> str:
        """Appelle l'API Groq via urllib (gratuit, format OpenAI-compatible)."""
        url = "https://api.groq.com/openai/v1/chat/completions"

        # Essayer chaque modèle jusqu'à ce qu'un fonctionne
        last_error = ""
        for model in self.GROQ_MODELS:
            payload = json.dumps({
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1024
            }).encode('utf-8')

            req = urllib_request.Request(url, data=payload, method='POST')
            req.add_header('User-Agent', 'ADALM2000-Oscilloscope/1.0')
            req.add_header('Content-Type', 'application/json')
            req.add_header('Authorization', f'Bearer {self.api_key}')

            try:
                with urllib_request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    return data['choices'][0]['message']['content']
            except Exception as e:
                error_msg = str(e)
                if hasattr(e, 'read'):
                    try:
                        body = json.loads(e.read().decode('utf-8'))
                        error_msg = body.get('error', {}).get('message', error_msg)
                    except Exception:
                        pass
                last_error = error_msg
                # Rate limit ou modèle indisponible → essayer le suivant
                continue

        raise ConnectionError(
            f"Aucun modèle Groq disponible.\n"
            f"Dernière erreur : {last_error}\n\n"
            f"Vérifiez que votre clé API est valide sur :\n"
            f"https://console.groq.com/keys"
        )

    def _parse_response(self, response_text: str) -> dict:
        """Parse la réponse JSON de l'IA, avec tolérance aux blocs markdown."""
        text = response_text.strip()
        
        # Retirer les blocs ```json ... ``` si présents
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1).strip()
        
        # Tenter un parsing JSON direct
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Fallback : chercher le premier { ... } dans le texte
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Impossible de parser la réponse JSON de l'IA")

    def _execute_code(self, code: str, sample_rate: int, duration: float, 
                      n_samples: int) -> np.ndarray:
        """
        Exécute le code généré par l'IA dans un environnement restreint.
        Retourne le signal numpy résultant.
        """
        # Environnement sandbox — seuls numpy et math sont disponibles
        t = np.linspace(0, duration, n_samples, endpoint=False)
        
        sandbox_globals = {
            '__builtins__': {},  # Désactiver tous les builtins
            'np': np,
            'numpy': np,
            'math': math,
            'abs': abs,
            'min': min,
            'max': max,
            'int': int,
            'float': float,
            'range': range,
            'len': len,
        }
        
        sandbox_locals = {
            'sample_rate': sample_rate,
            'duration': duration,
            'n_samples': n_samples,
            't': t,
        }

        # Exécuter le code
        try:
            exec(code, sandbox_globals, sandbox_locals)
        except Exception as e:
            raise RuntimeError(f"Erreur dans le code généré : {type(e).__name__}: {e}")

        # Récupérer le signal
        if 'signal' not in sandbox_locals:
            raise ValueError(
                "Le code généré ne définit pas de variable 'signal'.\n"
                "Le code doit créer : signal = np.array(...)"
            )

        signal = sandbox_locals['signal']
        
        if not isinstance(signal, np.ndarray):
            signal = np.array(signal, dtype=np.float64)

        if signal.ndim != 1:
            signal = signal.flatten()

        # S'assurer de la bonne taille
        if len(signal) != n_samples:
            # Interpolation ou troncature
            if len(signal) > n_samples:
                signal = signal[:n_samples]
            else:
                signal = np.pad(signal, (0, n_samples - len(signal)), mode='constant')

        # Clamp entre -5V et +5V (limites hardware ADALM2000)
        signal = np.clip(signal, -5.0, 5.0)

        return signal.astype(np.float64)
