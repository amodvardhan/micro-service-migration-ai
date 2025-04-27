// src/types/index.ts
export interface Repository {
    repo_id: string;
    repo_url: string;
    status: 'processing' | 'completed' | 'failed';
    timestamp: string;
}

export interface Entity {
    name: string;
    type: string;
    namespace?: string;
    properties?: Property[];
    methods?: Method[];
    file_path?: string;
}

export interface Property {
    name: string;
    type: string;
    access: string;
}

export interface Method {
    name: string;
    return_type: string;
    parameters: string;
    access: string;
}

export interface ApiEndpoint {
    route: string;
    method: string;
    handler: string;
    return_type?: string;
}

export interface Service {
    name: string;
    description?: string;
    responsibilities?: string[];
    entities?: string[];
    apis?: string[];
    files?: string[];
    namespace?: string;
}

export interface Dependency {
    source: string;
    target: string;
    type: string;
    description?: string;
}

export interface ServiceDependency {
    target: string;
    type: string;
    description?: string;
}

export interface AnalysisResults {
    architecture_type: string;
    potential_services: Service[];
    entities: Entity[];
    api_endpoints: ApiEndpoint[];
    dependencies: Dependency[];
    semantic_insights?: any;
}

export interface Analysis {
    repo_id: string;
    repo_url: string;
    status: 'processing' | 'completed' | 'failed';
    timestamp: string;
    error?: string;
    analysis?: AnalysisResults;
}

export interface GraphNode {
    id: string;
    name: string;
    val: number;
    color: string;
}

export interface GraphLink {
    source: string;
    target: string;
    value: number;
    type: string;
}

export interface GraphData {
    nodes: GraphNode[];
    links: GraphLink[];
}

export interface CodeSearchResult {
    id: string;
    content: string;
    metadata: {
        file_path: string;
        language: string;
        size: number;
        [key: string]: any;
    };
    similarity: number;
}

export interface SearchResults {
    query: string;
    results: CodeSearchResult[];
}
