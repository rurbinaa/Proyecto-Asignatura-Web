import { setupServer } from 'msw/node';
import { handlers } from './handlers';

/** MSW server instance — used to intercept HTTP at the network level. */
export const server = setupServer(...handlers);
