import type { ProjectCreate, SprintCreate, Task, GoalTree } from './types';
import type { WizardStep1Data } from './schemas';

/**
 * Sample goal data for onboarding tutorial
 * Demonstrates a simple "Hello World API" project with realistic tasks
 */

export const SAMPLE_PROJECT: ProjectCreate = {
  name: 'Hello World API',
  description: 'A simple REST API that returns "Hello, World!" - perfect for learning FoundrAI',
};

export const SAMPLE_WIZARD_STEP1: WizardStep1Data = {
  name: 'Hello World API',
  description: 'A simple REST API that returns "Hello, World!" - perfect for learning FoundrAI',
  workingDir: '/tmp/hello-world-api',
};

export const SAMPLE_SPRINT: SprintCreate = {
  goal: 'Build a REST API with a /hello endpoint that returns "Hello, World!" in JSON format',
};

export const SAMPLE_GOAL_TREE: Omit<GoalTree, 'sprint_id'> = {
  goal: 'Build a REST API with a /hello endpoint that returns "Hello, World!" in JSON format',
  tasks: [
    {
      task_id: 'sample-task-1',
      title: 'Design API specification',
      status: 'completed',
      children: [],
    },
    {
      task_id: 'sample-task-2',
      title: 'Implement /hello endpoint',
      status: 'completed',
      children: [
        {
          task_id: 'sample-task-2-1',
          title: 'Set up FastAPI application',
          status: 'completed',
          children: [],
        },
        {
          task_id: 'sample-task-2-2',
          title: 'Create hello endpoint handler',
          status: 'completed',
          children: [],
        },
      ],
    },
    {
      task_id: 'sample-task-3',
      title: 'Write tests',
      status: 'completed',
      children: [],
    },
    {
      task_id: 'sample-task-4',
      title: 'Add documentation',
      status: 'in_progress',
      children: [],
    },
  ],
};

export const SAMPLE_TASKS: Omit<Task, 'sprint_id' | 'created_at' | 'updated_at'>[] = [
  {
    task_id: 'sample-task-1',
    title: 'Design API specification',
    description: 'Define the API contract for the /hello endpoint including request/response format',
    acceptance_criteria: [
      'OpenAPI/Swagger specification created',
      'Response format defined (JSON with "message" field)',
      'HTTP status codes documented',
    ],
    assigned_to: 'ProductManager',
    priority: 1,
    status: 'completed',
    dependencies: [],
    result: {
      specification: 'GET /hello returns {"message": "Hello, World!"}',
      status_code: 200,
    },
    review: {
      approved: true,
      comments: 'Clear and simple specification',
    },
  },
  {
    task_id: 'sample-task-2',
    title: 'Implement /hello endpoint',
    description: 'Create FastAPI application with a GET /hello route',
    acceptance_criteria: [
      'FastAPI app initialized',
      '/hello endpoint returns correct JSON response',
      'Endpoint is accessible via HTTP GET',
    ],
    assigned_to: 'Developer',
    priority: 2,
    status: 'completed',
    dependencies: ['sample-task-1'],
    result: {
      files_created: ['main.py', 'requirements.txt'],
      endpoint: 'GET /hello',
    },
    review: {
      approved: true,
      comments: 'Clean implementation, follows best practices',
    },
  },
  {
    task_id: 'sample-task-3',
    title: 'Write tests',
    description: 'Create unit and integration tests for the /hello endpoint',
    acceptance_criteria: [
      'Test for successful 200 response',
      'Test for correct JSON structure',
      'All tests passing',
    ],
    assigned_to: 'QAEngineer',
    priority: 3,
    status: 'completed',
    dependencies: ['sample-task-2'],
    result: {
      test_file: 'test_main.py',
      tests_passed: 3,
      coverage: 100,
    },
    review: {
      approved: true,
      comments: 'Excellent test coverage',
    },
  },
  {
    task_id: 'sample-task-4',
    title: 'Add documentation',
    description: 'Write README with setup instructions and API usage examples',
    acceptance_criteria: [
      'README.md created',
      'Installation instructions included',
      'Usage examples provided',
    ],
    assigned_to: 'Developer',
    priority: 4,
    status: 'in_progress',
    dependencies: ['sample-task-2'],
    result: null,
    review: null,
  },
];

/**
 * Helper function to check if current project is using sample goal
 */
export function isSampleGoal(projectName: string): boolean {
  return projectName === SAMPLE_PROJECT.name;
}

/**
 * Helper function to get sample task by ID
 */
export function getSampleTask(taskId: string): Omit<Task, 'sprint_id' | 'created_at' | 'updated_at'> | undefined {
  return SAMPLE_TASKS.find((task) => task.task_id === taskId);
}
