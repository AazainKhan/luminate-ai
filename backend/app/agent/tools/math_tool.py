"""
MathTool - Symbolic computation helper for math problems

Based on Adarsh's MathTool pattern:
- Uses SymPy for symbolic algebra (equations, derivatives, integrals)
- Optional Wolfram Alpha integration for complex computations
- Normalizes problem input to handle common patterns

Features:
- Equation solving (single and systems)
- Variable substitution (e.g., "3x + y = 12 for y = 1")
- Derivative and integral computation
- Matrix operations
"""

import os
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MathTool:
    """
    Symbolic computation tool for mathematical problem solving.
    
    Provides:
    - SymPy-based symbolic computation (equations, calculus, matrices)
    - Optional Wolfram Alpha fallback for complex queries
    - Problem normalization (strips verbs, handles substitutions)
    """

    def __init__(self):
        self.app_id = os.getenv("WOLFRAM_APP_ID")
        self._sympy_available = self._check_sympy()
    
    def _check_sympy(self) -> bool:
        """Check if SymPy is available."""
        try:
            import sympy
            return True
        except ImportError:
            logger.warning("[MathTool] SymPy not available - computations will be limited")
            return False

    def _wolfram(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Try Wolfram Alpha for computation (if configured).
        
        Returns structured result or None if failed/not configured.
        """
        if not self.app_id:
            return None
        
        try:
            import requests
            url = "https://api.wolframalpha.com/v1/result"
            r = requests.get(
                url, 
                params={"i": prompt, "appid": self.app_id}, 
                timeout=8
            )
            if r.ok:
                return {
                    "tool": "wolframalpha",
                    "input": prompt,
                    "result_text": r.text,
                    "result_latex": None,
                    "raw": {"endpoint": "short"},
                    "success": True
                }
        except Exception as e:
            logger.debug(f"[MathTool] Wolfram failed: {e}")
        
        return None

    def _sympy(self, prompt: str) -> Dict[str, Any]:
        """
        Use SymPy for symbolic computation.
        
        Handles:
        - Single equations: "2x + 3 = 7"
        - Systems: "x + y = 5; x - y = 1"
        - Substitutions: "3x + y = 12 for y = 1"
        - Expressions: "diff(x^2, x)" or "integrate(2x, x)"
        """
        if not self._sympy_available:
            return {
                "tool": "sympy",
                "input": prompt,
                "result_text": "SymPy not available for computation",
                "result_latex": None,
                "raw": {},
                "success": False
            }
        
        try:
            from sympy import (
                Eq, sympify, symbols, Symbol, diff, integrate, limit, 
                Matrix, simplify, expand, factor, solve as sympy_solve,
                oo, sin, cos, tan, exp, log, sqrt, pi, E
            )
            from sympy.parsing.sympy_parser import (
                parse_expr, standard_transformations, 
                implicit_multiplication_application,
                convert_xor
            )
            
            transformations = standard_transformations + (implicit_multiplication_application, convert_xor)
            
            def safe_parse(expr_str: str):
                """Safely parse an expression string."""
                # Replace ^ with ** for exponents
                expr_str = expr_str.replace("^", "**")
                # Handle implicit multiplication like 2x → 2*x
                return parse_expr(expr_str, transformations=transformations, evaluate=False)
            
            # Handle 'for' clauses (substitutions)
            # e.g., "3x + y = 12 for y = 1" → solve with y=1 substituted
            if ' for ' in prompt.lower():
                return self._handle_substitution(prompt, safe_parse, Eq, sympy_solve)
            
            # Handle calculus operations
            if any(op in prompt.lower() for op in ['derivative', 'diff', 'integrate', 'integral', 'limit']):
                return self._handle_calculus(prompt, safe_parse, diff, integrate, limit, oo, Symbol)
            
            # Handle standard equations/systems
            return self._handle_equations(prompt, safe_parse, Eq, sympy_solve, simplify)

        except Exception as e:
            import traceback
            logger.error(f"[MathTool] SymPy error: {e}")
            return {
                "tool": "sympy",
                "input": prompt,
                "result_text": f"Computation error: {str(e)}",
                "result_latex": None,
                "raw": {"error": str(e), "traceback": traceback.format_exc()},
                "success": False
            }
    
    def _handle_substitution(self, prompt: str, safe_parse, Eq, sympy_solve) -> Dict[str, Any]:
        """Handle problems with 'for' substitution clauses."""
        try:
            # Split on 'for'
            main_part, subs_part = prompt.lower().split(' for ', 1)
            main_part = main_part.strip()
            subs_part = subs_part.strip()
            
            # Parse substitutions
            subs = {}
            for piece in subs_part.split(','):
                if '=' in piece:
                    var, val = piece.split('=', 1)
                    var = var.strip()
                    val = val.strip()
                    try:
                        subs[var] = safe_parse(val)
                    except:
                        subs[var] = float(val) if val.replace('.','',1).replace('-','',1).isdigit() else val
            
            # Parse main equation
            if '=' in main_part:
                left, right = main_part.split('=', 1)
                left_expr = safe_parse(left.strip())
                right_expr = safe_parse(right.strip())
                
                # Substitute values
                left_subbed = left_expr.subs(subs)
                right_subbed = right_expr.subs(subs)
                
                eq = Eq(left_subbed, right_subbed)
                
                # Get remaining variables
                free_vars = list(eq.free_symbols)
                
                if free_vars:
                    sol = sympy_solve(eq, free_vars)
                    if sol:
                        if isinstance(sol, list):
                            result_text = ", ".join([f"{v} = {s}" for v, s in zip(free_vars, sol)])
                        elif isinstance(sol, dict):
                            result_text = ", ".join([f"{k} = {v}" for k, v in sol.items()])
                        else:
                            result_text = str(sol)
                    else:
                        result_text = "No solution found"
                else:
                    # Both sides should be equal after substitution
                    result_text = f"After substitution: {left_subbed} = {right_subbed} → {left_subbed == right_subbed}"
            else:
                # Just an expression to evaluate
                expr = safe_parse(main_part)
                result = expr.subs(subs)
                result_text = str(result)
            
            return {
                "tool": "sympy",
                "input": prompt,
                "result_text": result_text,
                "result_latex": None,
                "raw": {"substitutions": str(subs)},
                "success": True
            }
            
        except Exception as e:
            return {
                "tool": "sympy",
                "input": prompt,
                "result_text": f"Substitution error: {str(e)}",
                "result_latex": None,
                "raw": {"error": str(e)},
                "success": False
            }
    
    def _handle_calculus(self, prompt: str, safe_parse, diff, integrate, limit, oo, Symbol) -> Dict[str, Any]:
        """Handle calculus operations (derivatives, integrals, limits)."""
        try:
            prompt_lower = prompt.lower()
            
            # Extract the expression (after the operation keyword)
            expr_match = re.search(r'(?:derivative|diff|integrate|integral|limit)\s+(?:of\s+)?(.+?)(?:\s+(?:with respect to|wrt|w\.r\.t\.?)\s+(\w+))?(?:\s+(?:from|at)\s+(.+))?$', prompt_lower)
            
            if not expr_match:
                # Try simpler pattern
                expr_match = re.search(r'(?:d/d(\w))\s*\((.+)\)', prompt_lower)
                if expr_match:
                    var = expr_match.group(1)
                    expr_str = expr_match.group(2)
                    expr = safe_parse(expr_str)
                    result = diff(expr, Symbol(var))
                    return {
                        "tool": "sympy",
                        "input": prompt,
                        "result_text": str(result),
                        "result_latex": None,
                        "raw": {"operation": "derivative"},
                        "success": True
                    }
            
            if expr_match:
                expr_str = expr_match.group(1).strip()
                var_str = expr_match.group(2) if expr_match.lastindex >= 2 and expr_match.group(2) else 'x'
                
                expr = safe_parse(expr_str)
                var = Symbol(var_str)
                
                if 'derivative' in prompt_lower or 'diff' in prompt_lower:
                    result = diff(expr, var)
                    operation = "derivative"
                elif 'integral' in prompt_lower or 'integrate' in prompt_lower:
                    result = integrate(expr, var)
                    operation = "integral"
                elif 'limit' in prompt_lower:
                    # Default limit as x → 0
                    result = limit(expr, var, 0)
                    operation = "limit"
                else:
                    result = expr
                    operation = "parse"
                
                return {
                    "tool": "sympy",
                    "input": prompt,
                    "result_text": str(result),
                    "result_latex": None,
                    "raw": {"operation": operation},
                    "success": True
                }
            
            return {
                "tool": "sympy",
                "input": prompt,
                "result_text": "Could not parse calculus expression",
                "result_latex": None,
                "raw": {},
                "success": False
            }
            
        except Exception as e:
            return {
                "tool": "sympy",
                "input": prompt,
                "result_text": f"Calculus error: {str(e)}",
                "result_latex": None,
                "raw": {"error": str(e)},
                "success": False
            }
    
    def _handle_equations(self, prompt: str, safe_parse, Eq, sympy_solve, simplify) -> Dict[str, Any]:
        """Handle standard equation solving."""
        try:
            # Split by semicolons for multiple equations
            parts = [p.strip() for p in prompt.split(';') if p.strip()]
            
            equations = []
            for part in parts:
                if '=' in part:
                    left, right = part.split('=', 1)
                    left_expr = safe_parse(left.strip())
                    right_expr = safe_parse(right.strip())
                    equations.append(Eq(left_expr, right_expr))
            
            if not equations:
                # Try to simplify as expression
                expr = safe_parse(prompt)
                simplified = simplify(expr)
                return {
                    "tool": "sympy",
                    "input": prompt,
                    "result_text": str(simplified),
                    "result_latex": None,
                    "raw": {"simplified": True},
                    "success": True
                }
            
            # Collect all variables
            all_vars = set()
            for eq in equations:
                all_vars.update(eq.free_symbols)
            all_vars = list(all_vars)
            
            # Solve
            if all_vars:
                sol = sympy_solve(equations, all_vars, dict=True)
                if sol:
                    if isinstance(sol, list) and len(sol) > 0:
                        # Format solutions
                        results = []
                        for s in sol:
                            results.append(", ".join([f"{k} = {v}" for k, v in s.items()]))
                        result_text = "; ".join(results)
                    else:
                        result_text = str(sol)
                else:
                    result_text = "No solution found"
            else:
                result_text = "No variables to solve for"
            
            return {
                "tool": "sympy",
                "input": prompt,
                "result_text": result_text,
                "result_latex": None,
                "raw": {"num_equations": len(equations)},
                "success": True
            }
            
        except Exception as e:
            return {
                "tool": "sympy",
                "input": prompt,
                "result_text": f"Equation solving error: {str(e)}",
                "result_latex": None,
                "raw": {"error": str(e)},
                "success": False
            }

    def normalize_problem(self, problem: str) -> Dict[str, Any]:
        """
        Normalize a math problem for computation.
        
        - Strips leading verbs (solve, compute, calculate, etc.)
        - Converts 'for' clauses to semicolon format
        - Extracts topic hints
        
        Returns:
            {
                "original_problem": str,
                "clean_problem": str,
                "compute_prompt": str,
                "topic_hint": Optional[str],
                "substitutions": Dict[str, str]
            }
        """
        original = (problem or "").strip()
        clean = original
        
        # Strip common leading verbs
        verbs = ["solve", "compute", "calculate", "find", "evaluate", "determine", "what is", "what are"]
        for verb in verbs:
            clean = re.sub(rf"^\s*{verb}\s+", "", clean, flags=re.IGNORECASE)
        
        substitutions: Dict[str, str] = {}
        compute_prompt = clean
        
        # Handle 'for' clauses
        match = re.search(r"\bfor\b(.+)", clean, flags=re.IGNORECASE)
        if match:
            main_part = clean[:match.start()].strip()
            tail = match.group(1).strip()
            if "=" in tail:
                compute_prompt = f"{main_part}; {tail}"
                for piece in tail.split(","):
                    if "=" in piece:
                        var, val = piece.split("=", 1)
                        substitutions[var.strip()] = val.strip()
        
        # Detect topic hint
        topic_hint: Optional[str] = None
        topic_keywords = [
            "derivative", "integral", "limit", "probability", "matrix",
            "regression", "gradient", "system of equations", "quadratic"
        ]
        for keyword in topic_keywords:
            if keyword.lower() in original.lower():
                topic_hint = keyword
                break
        
        return {
            "original_problem": original,
            "clean_problem": clean,
            "compute_prompt": compute_prompt,
            "topic_hint": topic_hint,
            "substitutions": substitutions
        }

    def compute(self, prompt: str) -> Dict[str, Any]:
        """
        Compute a math problem.
        
        Tries Wolfram Alpha first (if configured), then SymPy.
        
        Returns structured result with:
            - tool: "wolframalpha" or "sympy"
            - input: original prompt
            - result_text: human-readable result
            - result_latex: LaTeX representation (if available)
            - raw: additional computation details
            - success: whether computation succeeded
        """
        # Normalize the problem first
        normalized = self.normalize_problem(prompt)
        compute_prompt = normalized["compute_prompt"]
        
        logger.info(f"[MathTool] Computing: {compute_prompt[:50]}...")
        
        # Try Wolfram first
        wolfram_result = self._wolfram(compute_prompt)
        if wolfram_result and wolfram_result.get("success"):
            logger.info("[MathTool] Wolfram succeeded")
            return wolfram_result
        
        # Fall back to SymPy
        sympy_result = self._sympy(compute_prompt)
        logger.info(f"[MathTool] SymPy result: {sympy_result.get('success')}")
        return sympy_result


# Singleton instance
_math_tool_instance: Optional[MathTool] = None


def get_math_tool() -> MathTool:
    """Get or create MathTool singleton."""
    global _math_tool_instance
    if _math_tool_instance is None:
        _math_tool_instance = MathTool()
    return _math_tool_instance
