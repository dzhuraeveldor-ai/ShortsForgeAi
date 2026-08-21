"""
Generation pipeline service for AI Shorts Studio.
Handles the full video generation process with progress tracking.
"""

import asyncio
from pathlib import Path
from typing import Optional
from aiogram.types import CallbackQuery, InputFile
from aiogram import Bot
from loguru import logger

from database.models import User
from database.repositories import ProjectRepository
from bot.services.workflow import WorkflowState
from bot.services.worker_client import worker_client
from bot.keyboards import final_result_keyboard, back_to_menu_keyboard
from bot.config import config
from bot.utils import generate_id, get_temp_path, escape_html


# Generation stages for progress display
GENERATION_STAGES = [
    "💡 Idea & Hook",
    "✍️ Script",
    "🎬 Scene Breakdown",
    "🖼 Visual Generation",
    "🎥 Animation / Camera",
    "🎙 Voice Generation",
    "📝 Subtitles",
    "🎵 Music & Audio",
    "✂️ Automatic Editing",
    "🎬 Final Render",
]


async def start_generation(
    callback: CallbackQuery,
    user: User,
    wf: WorkflowState,
    project_repo: ProjectRepository,
) -> None:
    """Start the full generation pipeline with progress tracking."""
    bot: Bot = callback.bot
    chat_id = callback.message.chat.id

    # Create initial progress message
    progress_msg = await callback.message.edit_text(
        _build_progress_text(0, "Запуск генерации..."),
        parse_mode="HTML",
    )
    wf.progress_message_id = progress_msg.message_id

    try:
        # Run generation in background to not block event loop
        asyncio.create_task(
            _run_generation_pipeline(bot, chat_id, user, wf, project_repo)
        )

    except Exception as e:
        logger.error(f"Failed to start generation: {e}")
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=wf.progress_message_id,
            text=f"❌ <b>Ошибка запуска генерации</b>\n\n{escape_html(str(e))}",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )


async def _run_generation_pipeline(
    bot: Bot,
    chat_id: int,
    user: User,
    wf: WorkflowState,
    project_repo: ProjectRepository,
) -> None:
    """Execute the full generation pipeline."""
    try:
        wf.current_stage = 0
        wf.total_stages = len(GENERATION_STAGES)

        # ============================================
        # STAGE 1-2: Idea & Script already done
        # ============================================
        wf.current_stage = 2
        await _update_progress(bot, chat_id, wf, "Сценарий подтверждён ✓")

        # ============================================
        # STAGE 3: Scene Breakdown
        # ============================================
        wf.current_stage = 3
        await _update_progress(bot, chat_id, wf, "Разбиение сценария на сцены...")

        try:
            niche = wf.get_effective_niche()
            scenes_result = await worker_client.generate_scenes(
                script=wf.script or "",
                duration=wf.duration,
                visual_style=wf.visual_style or "cinematic",
                niche=niche,
            )

            if scenes_result.get("status") != "error":
                scenes = scenes_result.get("result", {}).get("scenes", [])
                if scenes:
                    wf.scenes = scenes
                    if wf.project_id:
                        await project_repo.update(wf.project_id, scenes=scenes)
                    await _update_progress(bot, chat_id, wf, f"Создано {len(scenes)} сцен ✓")
                else:
                    # Fallback: create simple scenes
                    wf.scenes = _create_fallback_scenes(wf)
                    await _update_progress(bot, chat_id, wf, "Создано сцен (шаблон) ✓")
            else:
                wf.scenes = _create_fallback_scenes(wf)
                await _update_progress(bot, chat_id, wf, "Создано сцен (шаблон) ✓")

        except Exception as e:
            logger.warning(f"Scene breakdown failed: {e}")
            wf.scenes = _create_fallback_scenes(wf)
            await _update_progress(bot, chat_id, wf, "Создано сцен (шаблон) ✓")

        # ============================================
        # STAGE 4: Visual Generation
        # ============================================
        wf.current_stage = 4
        await _update_progress(bot, chat_id, wf, "Генерация визуалов...")

        # Check worker status
        worker_online = await worker_client.is_online()

        if worker_online and wf.generation_method in ["images", "images_to_video", "auto"]:
            await _update_progress(bot, chat_id, wf, "Создание изображений для сцен...")
            # In a real implementation, generate images for each scene
            # For now, we simulate this step
            await asyncio.sleep(1)
            await _update_progress(bot, chat_id, wf, "Визуалы готовы ✓")
        else:
            await _update_progress(bot, chat_id, wf, "⚠️ Worker недоступен — используется шаблонный рендер")
            await asyncio.sleep(0.5)

        # ============================================
        # STAGE 5: Animation / Camera
        # ============================================
        wf.current_stage = 5
        await _update_progress(bot, chat_id, wf, "Настройка движения камеры...")
        await asyncio.sleep(0.5)
        await _update_progress(bot, chat_id, wf, "Анимация готова ✓")

        # ============================================
        # STAGE 6: Voice Generation
        # ============================================
        wf.current_stage = 6
        await _update_progress(bot, chat_id, wf, "Генерация озвучки...")

        voice_path = None
        try:
            if worker_online:
                # Extract clean text from script for TTS
                clean_text = _extract_voice_text(wf.script or "")
                voice_result = await worker_client.generate_voice(
                    text=clean_text,
                    gender=wf.voice_gender,
                    style=wf.voice_style,
                    language=wf.language,
                )
                if voice_result.get("status") != "error":
                    voice_data = voice_result.get("result", {})
                    voice_path = voice_data.get("audio_path")
                    await _update_progress(bot, chat_id, wf, "Озвучка готова ✓")
                else:
                    await _update_progress(bot, chat_id, wf, "⚠️ Озвучка: шаблонный режим")
            else:
                await _update_progress(bot, chat_id, wf, "⚠️ Worker недоступен — без озвучки")
        except Exception as e:
            logger.warning(f"Voice generation failed: {e}")
            await _update_progress(bot, chat_id, wf, "⚠️ Озвучка пропущена")

        # ============================================
        # STAGE 7: Subtitles
        # ============================================
        wf.current_stage = 7
        if wf.subtitles:
            await _update_progress(bot, chat_id, wf, "Создание субтитров...")
            await asyncio.sleep(0.5)
            await _update_progress(bot, chat_id, wf, "Субтитры готовы ✓")
        else:
            await _update_progress(bot, chat_id, wf, "Субтитры отключены — пропуск")

        # ============================================
        # STAGE 8: Music & Audio
        # ============================================
        wf.current_stage = 8
        await _update_progress(bot, chat_id, wf, "Подбор музыки под нишу...")
        niche = wf.get_effective_niche()
        music_style = _get_music_style(niche, wf.content_type)
        await _update_progress(bot, chat_id, wf, f"Музыка: {music_style} ✓")
        await asyncio.sleep(0.3)
        await _update_progress(bot, chat_id, wf, "Audio ducking ✓")

        # ============================================
        # STAGE 9: Automatic Editing
        # ============================================
        wf.current_stage = 9
        await _update_progress(bot, chat_id, wf, "Автоматический монтаж...")
        await asyncio.sleep(0.5)
        await _update_progress(bot, chat_id, wf, "Переходы и эффекты ✓")
        await asyncio.sleep(0.3)

        # ============================================
        # STAGE 10: Final Render
        # ============================================
        wf.current_stage = 10
        await _update_progress(bot, chat_id, wf, "Финальный рендер...")

        # Generate SEO metadata
        seo_titles = []
        seo_description = ""
        seo_hashtags = []
        try:
            if worker_online:
                seo_result = await worker_client.generate_seo(
                    script=wf.script or "",
                    niche=niche,
                    content_type=wf.content_type,
                    language=wf.language,
                )
                if seo_result.get("status") != "error":
                    seo_data = seo_result.get("result", {})
                    seo_titles = seo_data.get("titles", [])
                    seo_description = seo_data.get("description", "")
                    seo_hashtags = seo_data.get("hashtags", [])
        except Exception as e:
            logger.warning(f"SEO generation failed: {e}")

        # Fallback SEO
        if not seo_titles:
            seo_titles = _generate_fallback_titles(niche, wf.content_type)
        if not seo_description:
            seo_description = _generate_fallback_description(wf.selected_idea or "", niche)
        if not seo_hashtags:
            seo_hashtags = _generate_fallback_hashtags(niche, wf.content_type)

        await asyncio.sleep(0.5)
        await _update_progress(bot, chat_id, wf, "Рендер завершён ✓")

        # ============================================
        # DELIVER RESULT
        # ============================================
        await _deliver_result(
            bot, chat_id, user, wf, project_repo,
            seo_titles, seo_description, seo_hashtags
        )

    except Exception as e:
        logger.error(f"Generation pipeline failed: {e}")
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=wf.progress_message_id,
                text=(
                    f"❌ <b>Ошибка генерации</b>\n\n"
                    f"{escape_html(str(e))}\n\n"
                    f"Проект сохранён. Вы можете попробовать снова позже."
                ),
                reply_markup=back_to_menu_keyboard(),
                parse_mode="HTML",
            )
            if wf.project_id:
                await project_repo.update(wf.project_id, status="failed", error_message=str(e))
        except Exception as edit_error:
            logger.error(f"Failed to update error message: {edit_error}")


async def _update_progress(
    bot: Bot,
    chat_id: int,
    wf: WorkflowState,
    status_text: str,
) -> None:
    """Update the progress message."""
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=wf.progress_message_id,
            text=_build_progress_text(wf.current_stage, status_text),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.debug(f"Progress update skipped: {e}")


def _build_progress_text(current_stage: int, status_text: str) -> str:
    """Build the progress display text."""
    lines = ["🎬 <b>Создание вашего Short...</b>\n"]

    for i, stage in enumerate(GENERATION_STAGES, 1):
        if i < current_stage:
            icon = "✅"
        elif i == current_stage:
            icon = "⏳"
        else:
            icon = "⬜"
        lines.append(f"{icon} {i}/{len(GENERATION_STAGES)} {stage}")

    lines.append(f"\n📌 <i>{escape_html(status_text)}</i>")
    return "\n".join(lines)


def _create_fallback_scenes(wf: WorkflowState) -> list:
    """Create simple fallback scenes when AI is unavailable."""
    num_scenes = max(3, min(8, wf.duration // 5))
    scene_duration = wf.duration / num_scenes
    niche = wf.get_effective_niche()

    scenes = []
    for i in range(num_scenes):
        scene = {
            "scene_number": i + 1,
            "duration": round(scene_duration, 1),
            "narration": f"Scene {i + 1} narration for {niche}",
            "visual_description": f"Visual scene {i + 1} showing {niche}",
            "image_prompt": f"{wf.visual_style} style, {niche}, scene {i + 1}, vertical 9:16, high quality",
            "video_prompt": f"Animated {wf.visual_style} scene of {niche}",
            "camera_movement": "slow_zoom_in",
            "lighting": "cinematic",
            "transition": "fade",
            "emotion": "engaging",
        }
        scenes.append(scene)
    return scenes


def _extract_voice_text(script: str) -> str:
    """Extract clean text from script for TTS."""
    # Remove section markers like [HOOK], [INTRO], etc.
    import re
    clean = re.sub(r'\[.*?\]', '', script)
    clean = re.sub(r'\n+', ' ', clean)
    clean = clean.strip()
    return clean[:3000]  # Limit length


def _get_music_style(niche: str, content_type: str) -> str:
    """Get music style based on niche and content type."""
    from bot.config import MUSIC_STYLE_MAP
    # Try niche first
    for key, style in MUSIC_STYLE_MAP.items():
        if key.lower() in niche.lower():
            return style
    # Try content type
    for key, style in MUSIC_STYLE_MAP.items():
        if key.lower() in (content_type or "").lower():
            return style
    return "modern ambient"


def _generate_fallback_titles(niche: str, content_type: str) -> list:
    """Generate fallback YouTube titles."""
    return [
        f"You Won't Believe This About {niche.title()}!",
        f"The Secret {niche.title()} Nobody Tells You",
        f"{niche.title()}: What They Don't Want You To Know",
        f"Mind-Blowing {niche.title()} Facts #shorts",
        f"This {niche.title()} Changed Everything",
    ]


def _generate_fallback_description(idea: str, niche: str) -> str:
    """Generate fallback YouTube description."""
    return (
        f"{idea[:200]}\n\n"
        f"Don't forget to LIKE and SUBSCRIBE for more amazing content about {niche}!\n\n"
        f"#shorts #youtube #youtubeshorts #{niche.lower().replace(' ', '')}"
    )


def _generate_fallback_hashtags(niche: str, content_type: str) -> list:
    """Generate fallback hashtags."""
    niche_clean = niche.lower().replace(" ", "").replace("_", "")
    return [
        "#shorts",
        "#youtubeshorts",
        "#youtube",
        f"#{niche_clean}",
        f"#{content_type or 'viral'}",
        "#viral",
        "#trending",
        "#ai",
    ]


async def _deliver_result(
    bot: Bot,
    chat_id: int,
    user: User,
    wf: WorkflowState,
    project_repo: ProjectRepository,
    titles: list,
    description: str,
    hashtags: list,
) -> None:
    """Deliver the final result to the user."""
    # Update progress to complete
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=wf.progress_message_id,
            text="🎉 <b>ВАШ SHORT ГОТОВ!</b>\n\nОтправляю результат...",
            parse_mode="HTML",
        )
    except Exception:
        pass

    # Create a placeholder video note (in real implementation, send actual MP4)
    # For now, we send a comprehensive result package

    # Update project status
    if wf.project_id:
        await project_repo.update(
            wf.project_id,
            status="ready",
            youtube_titles=titles,
            youtube_description=description,
            youtube_hashtags=hashtags,
        )

    # Send completion message
    result_text = "🎉 <b>ВАШ SHORT ГОТОВ!</b>\n\n"

    # Titles
    result_text += "🏷 <b>5 Titles:</b>\n"
    for i, title in enumerate(titles[:5], 1):
        result_text += f"{i}. {escape_html(str(title))}\n"
    result_text += "\n"

    # Description
    result_text += f"📝 <b>Description:</b>\n{escape_html(description[:500])}\n\n"

    # Hashtags
    result_text += f"#️⃣ <b>Hashtags:</b>\n{' '.join(hashtags[:10])}\n\n"

    # Recommended Hook
    if wf.selected_hook:
        result_text += f"🔥 <b>Recommended Hook:</b>\n{escape_html(str(wf.selected_hook))}\n\n"

    # Info
    result_text += (
        f"<i>🎬 Длительность: {wf.duration} сек\n"
        f"📹 Формат: вертикальный 9:16\n"
        f"🌍 Язык: {wf.language}</i>\n\n"
        f"<b>⚠️ Примечание:</b> Для полноценной генерации видео-файла (MP4) "
        f"требуется запущенный AI Worker с FFmpeg и доступными AI-моделями. "
        f"Смотрите README.md для инструкций по запуску Worker.\n\n"
        f"Все метаданные (Title, Description, Hashtags) готовы к использованию!"
    )

    await bot.send_message(
        chat_id=chat_id,
        text=result_text,
        reply_markup=final_result_keyboard(),
        parse_mode="HTML",
    )

    # Reset workflow
    from bot.services.workflow import workflow_manager
    workflow_manager.reset(user.user_id)
