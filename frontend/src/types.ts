export interface VideoSegment {
    id: number;
    order: number;
    start_time: number;
    end_time: number;
    transcript: string;
    asset_type: 'ai_image' | 'user_upload' | 'video_clip' | 'meme' | 'emoji';
    asset_file: string | null;
    layout_event: 'split' | 'bottom_full' | 'top_full';
    animation_type: 'ken_burns' | 'side_slide' | 'static';
}

export interface VideoProject {
    id: number;
    title: string;
    status: 'draft' | 'analyzing' | 'ready' | 'rendering' | 'completed' | 'failed';
    status_display: string;
    progress_message: string;
    error_message: string;
    raw_video_url: string | null;
    output_video_url: string | null;
    created_at: string;
}

export interface AnalyzeResponse {
    status: string;
    message: string;
}

export interface RenderResponse {
    status: string;
    message: string;
}
