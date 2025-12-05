#!/usr/bin/env python
"""
Run Model Comparison Tests

Runs the full model comparison test suite and generates reports.

Usage:
    python -m tests.model_comparison.run_comparison
    
Options:
    --models: Comma-separated list of models to test (default: all)
    --categories: Comma-separated list of categories (default: all)
    --roles: Comma-separated list of target roles to test (router,tutor,evaluator,rag,fast,complex)
    --output: Output directory for reports (default: test_output/model_comparison)
    --github-token: GitHub API token for GitHub Models
"""

import asyncio
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
from collections import defaultdict
from typing import List, Dict, Optional

from .test_cases import TEST_CASES, TestCategory, get_all_test_cases, get_test_cases_by_role
from .model_runner import ModelRunner
from .evaluator import ResponseEvaluator, EvaluationResult

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_report(results: List[EvaluationResult], output_dir: Path, model_configs: Dict) -> Dict:
    """Generate markdown and JSON reports from results."""
    
    # Group by model
    model_results = defaultdict(list)
    for result in results:
        model_results[result.model_name].append(result)
    
    # Calculate rankings
    rankings = []
    for model_name, model_data in model_results.items():
        avg_score = sum(r.overall_score for r in model_data) / len(model_data)
        avg_latency = sum(r.latency_ms for r in model_data) / len(model_data)
        total_cost = sum(r.cost_estimate for r in model_data)
        
        # Get model config info
        config = model_configs.get(model_name, {})
        provider = config.get("provider", "unknown")
        role = config.get("role", "general")
        
        # Category breakdown
        category_scores = defaultdict(list)
        for result in model_data:
            # Map test ID prefix to category
            prefix_map = {
                "ped_": "pedagogical", "fact_": "factual", "code_": "code", 
                "math_": "math", "inst_": "instruction_following",
                "router_": "router", "tutor_": "tutor", "eval_": "evaluator",
                "rag_": "rag", "fast_": "fast", "complex_": "complex"
            }
            for prefix, cat in prefix_map.items():
                if result.test_id.startswith(prefix):
                    category_scores[cat].append(result.overall_score)
                    break
        
        cat_avgs = {cat: sum(scores)/len(scores) for cat, scores in category_scores.items() if scores}
        
        rankings.append({
            "model_name": model_name,
            "provider": provider,
            "target_role": role,
            "avg_score": avg_score,
            "avg_latency_ms": avg_latency,
            "total_cost": total_cost,
            "category_scores": cat_avgs,
            "strengths": [cat for cat, score in cat_avgs.items() if score > 0.75],
            "weaknesses": [cat for cat, score in cat_avgs.items() if score < 0.5],
            "test_count": len(model_data),
        })
    
    # Sort by score
    rankings.sort(key=lambda x: x["avg_score"], reverse=True)
    
    # Generate role-based recommendations
    role_recommendations = {}
    for role in ["router", "tutor", "evaluator", "rag", "fast", "complex", "overall"]:
        best_model = None
        best_score = 0
        best_latency = float('inf')
        
        for r in rankings:
            # For role-specific categories, use category score
            if role in r["category_scores"]:
                score = r["category_scores"][role]
            else:
                score = r["avg_score"]
            
            # Prefer models targeting this role
            is_target_role = r["target_role"] == role
            adjusted_score = score * 1.1 if is_target_role else score
            
            if adjusted_score > best_score or (adjusted_score == best_score and r["avg_latency_ms"] < best_latency):
                best_score = adjusted_score
                best_latency = r["avg_latency_ms"]
                best_model = r["model_name"]
        
        if best_model:
            role_recommendations[role] = {
                "model": best_model,
                "score": min(best_score, 1.0),
                "latency_ms": best_latency,
            }
    
    # Map roles to intents
    intent_recommendations = {
        "tutor": role_recommendations.get("tutor", {}).get("model"),
        "math": role_recommendations.get("complex", {}).get("model"),
        "coder": role_recommendations.get("complex", {}).get("model"),
        "syllabus_query": role_recommendations.get("fast", {}).get("model"),
        "fast": role_recommendations.get("fast", {}).get("model"),
        "router": role_recommendations.get("router", {}).get("model"),
        "evaluator": role_recommendations.get("evaluator", {}).get("model"),
    }
    
    # Generate markdown report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_lines = [
        "# Model Comparison Report\n\n",
        f"**Generated:** {datetime.now().isoformat()}\n\n",
        f"**Total tests:** {len(results)}\n\n",
        f"**Models tested:** {len(model_results)}\n\n",
        "---\n\n",
        
        "## Executive Summary\n\n",
        "### Best Models by Role\n\n",
        "| Role | Recommended Model | Score | Latency |\n",
        "|------|-------------------|-------|--------|\n",
    ]
    
    for role, rec in role_recommendations.items():
        report_lines.append(
            f"| {role.title()} | **{rec['model']}** | {rec['score']:.2f} | {rec['latency_ms']:.0f}ms |\n"
        )
    
    report_lines.append("\n---\n\n")
    report_lines.append("## Overall Rankings\n\n")
    report_lines.append("| Rank | Model | Provider | Role | Avg Score | Latency | Cost | Tests |\n")
    report_lines.append("|------|-------|----------|------|-----------|---------|------|-------|\n")
    
    for i, r in enumerate(rankings, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        report_lines.append(
            f"| {emoji} | **{r['model_name']}** | {r['provider']} | {r['target_role']} | "
            f"{r['avg_score']:.2f} | {r['avg_latency_ms']:.0f}ms | "
            f"${r['total_cost']:.4f} | {r['test_count']} |\n"
        )
    
    report_lines.append("\n---\n\n")
    report_lines.append("## Category Performance Matrix\n\n")
    
    # Build category matrix header
    all_categories = set()
    for r in rankings:
        all_categories.update(r["category_scores"].keys())
    categories = sorted(all_categories)
    
    report_lines.append("| Model | " + " | ".join(categories) + " |\n")
    report_lines.append("|-------" + "|-------" * len(categories) + "|\n")
    
    for r in rankings:
        row = f"| {r['model_name']} |"
        for cat in categories:
            score = r["category_scores"].get(cat, 0)
            emoji = "✅" if score >= 0.75 else "⚠️" if score >= 0.5 else "❌"
            row += f" {emoji} {score:.2f} |"
        report_lines.append(row + "\n")
    
    report_lines.append("\n---\n\n")
    report_lines.append("## Model Details\n\n")
    
    for r in rankings:
        report_lines.append(f"### {r['model_name']}\n\n")
        report_lines.append(f"- **Provider:** {r['provider']}\n")
        report_lines.append(f"- **Target Role:** {r['target_role']}\n")
        report_lines.append(f"- **Average Score:** {r['avg_score']:.3f}\n")
        report_lines.append(f"- **Average Latency:** {r['avg_latency_ms']:.0f}ms\n")
        report_lines.append(f"- **Total Cost:** ${r['total_cost']:.4f}\n")
        
        if r["strengths"]:
            report_lines.append(f"- **Strengths:** {', '.join(r['strengths'])}\n")
        if r["weaknesses"]:
            report_lines.append(f"- **Weaknesses:** {', '.join(r['weaknesses'])}\n")
        
        report_lines.append("\n**Category Scores:**\n\n")
        for cat, score in sorted(r["category_scores"].items(), key=lambda x: -x[1]):
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            report_lines.append(f"- {cat}: `{bar}` {score:.2f}\n")
        
        report_lines.append("\n")
    
    report_lines.append("---\n\n")
    report_lines.append("## Recommended Agent Architecture\n\n")
    report_lines.append("Based on the test results, here's the recommended model assignment:\n\n")
    report_lines.append("```\n")
    report_lines.append("┌─────────────────────────────────────────────────────────────┐\n")
    report_lines.append("│                    LUMINATE AI AGENT                        │\n")
    report_lines.append("├─────────────────────────────────────────────────────────────┤\n")
    
    router_model = intent_recommendations.get("router", "N/A")
    tutor_model = intent_recommendations.get("tutor", "N/A")
    fast_model = intent_recommendations.get("fast", "N/A")
    eval_model = intent_recommendations.get("evaluator", "N/A")
    
    report_lines.append(f"│  Router/Supervisor:     {router_model:<35} │\n")
    report_lines.append(f"│  Tutor Agent:           {tutor_model:<35} │\n")
    report_lines.append(f"│  Fast/Syllabus:         {fast_model:<35} │\n")
    report_lines.append(f"│  Evaluator:             {eval_model:<35} │\n")
    report_lines.append("└─────────────────────────────────────────────────────────────┘\n")
    report_lines.append("```\n\n")
    
    report_lines.append("### Intent → Model Mapping\n\n")
    report_lines.append("| Intent | Recommended Model |\n")
    report_lines.append("|--------|-------------------|\n")
    for intent, model in intent_recommendations.items():
        if model:
            report_lines.append(f"| `{intent}` | {model} |\n")
    
    # Write report
    report_path = output_dir / f"report_{timestamp}.md"
    report_path.write_text("".join(report_lines))
    logger.info(f"📝 Report saved to: {report_path}")
    
    # Write JSON data
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "results": [asdict(r) for r in results],
        "rankings": rankings,
        "role_recommendations": role_recommendations,
        "intent_recommendations": intent_recommendations,
    }
    json_path = output_dir / f"results_{timestamp}.json"
    json_path.write_text(json.dumps(json_data, indent=2))
    logger.info(f"📊 JSON saved to: {json_path}")
    
    return {
        "rankings": rankings,
        "role_recommendations": role_recommendations,
        "intent_recommendations": intent_recommendations,
        "report_path": str(report_path),
        "json_path": str(json_path),
    }


async def run_comparison(
    models: List[str] = None,
    categories: List[str] = None,
    roles: List[str] = None,
    output_dir: str = "test_output/model_comparison",
    github_token: str = None,
) -> Dict:
    """Run the full model comparison test suite."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Filter test cases
    test_cases = get_all_test_cases()
    
    if categories:
        cat_enums = [TestCategory(c) for c in categories]
        test_cases = [tc for tc in test_cases if tc.category in cat_enums]
    
    if roles:
        # Filter by target role
        role_cases = []
        for role in roles:
            role_cases.extend(get_test_cases_by_role(role))
        test_cases = role_cases if role_cases else test_cases
    
    logger.info(f"🚀 Starting model comparison with {len(test_cases)} test cases")
    
    # Initialize components
    runner = ModelRunner(github_token=github_token)
    evaluator = ResponseEvaluator()
    
    # Get available models
    available_models = runner.get_available_models()
    models_to_test = models or available_models
    models_to_test = [m for m in models_to_test if m in available_models]
    
    if not models_to_test:
        logger.error("No models available for testing")
        return {"error": "No models available"}
    
    logger.info(f"📋 Testing models: {', '.join(models_to_test)}")
    
    all_results: List[EvaluationResult] = []
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"[{i}/{len(test_cases)}] Running test: {test_case.id} ({test_case.category.value})")
        
        # Run query against all models
        try:
            responses = await runner.run_comparison(test_case.query, models_to_test)
        except Exception as e:
            logger.error(f"  ❌ Failed to run comparison: {e}")
            continue
        
        # Evaluate each response
        for model_name, response in responses.items():
            if response.error:
                logger.warning(f"  ⚠️ {model_name}: {response.error}")
                continue
            
            result = evaluator.evaluate(
                test_case=test_case,
                model_name=model_name,
                response_text=response.response_text,
                latency_ms=response.latency_ms,
                cost_estimate=response.cost_estimate,
            )
            
            all_results.append(result)
            
            score_emoji = "✅" if result.overall_score >= 0.7 else "⚠️" if result.overall_score >= 0.5 else "❌"
            logger.info(
                f"  {score_emoji} {model_name}: score={result.overall_score:.2f}, "
                f"latency={result.latency_ms:.0f}ms"
            )
    
    # Clean up
    await runner.close()
    
    if not all_results:
        logger.error("No results collected")
        return {"error": "No results"}
    
    # Get model configs for report
    model_configs = {name: config for name, config in runner.MODELS_TO_TEST.items()}
    
    # Generate report
    report_data = generate_report(all_results, output_path, model_configs)
    
    # Print summary
    print("\n" + "=" * 70)
    print("MODEL COMPARISON SUMMARY")
    print("=" * 70)
    
    for i, r in enumerate(report_data["rankings"][:5], 1):  # Top 5
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
        print(f"\n{emoji} {r['model_name']} ({r['provider']})")
        print(f"   Score: {r['avg_score']:.2f} | Latency: {r['avg_latency_ms']:.0f}ms | Cost: ${r['total_cost']:.4f}")
        if r["strengths"]:
            print(f"   Strengths: {', '.join(r['strengths'])}")
        if r["weaknesses"]:
            print(f"   Weaknesses: {', '.join(r['weaknesses'])}")
    
    print("\n" + "-" * 70)
    print("RECOMMENDED MODEL ASSIGNMENTS")
    print("-" * 70)
    
    for role, rec in report_data["role_recommendations"].items():
        print(f"  {role:12} → {rec['model']:20} (score: {rec['score']:.2f}, {rec['latency_ms']:.0f}ms)")
    
    print("\n" + "-" * 70)
    print("INTENT ROUTING")
    print("-" * 70)
    
    for intent, model in report_data["intent_recommendations"].items():
        if model:
            print(f"  {intent:15} → {model}")
    
    print("=" * 70)
    print(f"\n📝 Full report: {report_data['report_path']}")
    
    return report_data


def main():
    parser = argparse.ArgumentParser(description="Run model comparison tests")
    parser.add_argument("--models", type=str, help="Comma-separated list of models")
    parser.add_argument("--categories", type=str, help="Comma-separated categories")
    parser.add_argument("--roles", type=str, help="Comma-separated target roles (router,tutor,evaluator,rag,fast,complex)")
    parser.add_argument("--output", type=str, default="test_output/model_comparison")
    parser.add_argument("--github-token", type=str, help="GitHub API token for GitHub Models")
    
    args = parser.parse_args()
    
    models = args.models.split(",") if args.models else None
    categories = args.categories.split(",") if args.categories else None
    roles = args.roles.split(",") if args.roles else None
    
    asyncio.run(run_comparison(
        models=models,
        categories=categories,
        roles=roles,
        output_dir=args.output,
        github_token=args.github_token,
    ))


if __name__ == "__main__":
    main()
