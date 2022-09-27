import pygame as pg
import Chess_Engine
import time
import json
from clients import Client
from constants import WHITE, BLACK, HEIGHT_BOARD, WIDTH_WINDOW, HEIGHT_WINDOW, DIMENSION, SQ_SIZE, MAX_FPS, PIECES, HOST, PORT


pg.init()
FONT=pg.font.Font(None, 32)
IMAGES = {piece: pg.transform.scale(pg.image.load('images/'+ piece+ '.png'), (SQ_SIZE, SQ_SIZE)) for piece in PIECES}
smallFont = pg.font.SysFont('arial', 20)
mediumFont = pg.font.SysFont('arial', 28)
largeFont = pg.font.SysFont('arial', 40)

class InputBox:

    def __init__(self, x, y, w, h, text='', COLOR_INACTIVE=pg.Color('lightskyblue3'), COLOR_ACTIVE = pg.Color('dodgerblue2')):
        self.rect = pg.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE

        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.FONT = FONT
        self.COLOR_INACTIVE = COLOR_INACTIVE
        self.COLOR_ACTIVE = COLOR_ACTIVE
        self.active = False

    def handle_event(self, event):

        if event.type == pg.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = self.COLOR_ACTIVE if self.active else self.COLOR_INACTIVE

        if event.type == pg.KEYDOWN:
            if self.active:
                # if event.key == pg.K_RETURN:
                #     print(self.text)
                #     self.text = ''
                if event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = self.FONT.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pg.draw.rect(screen, self.color, self.rect, 2)

    def disable(self):
        self.rect = None

def drawGameState(screen, gs):

    drawBoard(screen)
    drawPieces(screen, gs.board)

def drawBoard(screen):
    colors = [pg.Color('white'), pg.Color('gray')]
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = colors[((row+col)%2)]
            pg.draw.rect(screen, color, pg.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))


def drawPieces(screen, board):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != '--':
                screen.blit(IMAGES[piece], pg.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def main():

    def draw_button(left, top, width, height, text):
        buttonRect = pg.Rect(left, top, width, height)
        buttonText = mediumFont.render(text, True, BLACK)
        buttonTextRect = buttonText.get_rect()
        buttonTextRect.center = buttonRect.center
        pg.draw.rect(screen, WHITE, buttonRect)
        screen.blit(buttonText, buttonTextRect)
        return buttonRect, buttonText, buttonTextRect

    pg.init()
    screen = pg.display.set_mode((WIDTH_WINDOW, HEIGHT_WINDOW))
    clock = pg.time.Clock()
    screen.fill(pg.Color('white'))
    gs = Chess_Engine.GameState()

    running = True
    user_registred = False

    sqSelected = ()
    playerClicks = []


    login_input_box = InputBox((WIDTH_WINDOW / 4), (1 / 2) * HEIGHT_BOARD, WIDTH_WINDOW / 2, 50)
    num_match_input_box = InputBox((WIDTH_WINDOW / 4), (1 / 2) * HEIGHT_BOARD, WIDTH_WINDOW / 2, 50)

    moveMade = False

    is_my_step = None

    is_game = False
    is_past_matches_window = False
    is_past_matche_window = False
    matches = []

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if user_registred:
                    if not is_game:
                    # is_game = False
                        is_past_matches_window = False
                        is_past_matche_window = False
                    #print(gs.steps)
                    else:
                        running = False
                else:
                    running = False

            if not user_registred:

                # Login button
                buttonRect, buttonText, buttonTextRect = draw_button((WIDTH_WINDOW / 4), (3 / 4) * HEIGHT_WINDOW, WIDTH_WINDOW / 2, 50, text="Login")
                login_input_box.draw(screen)
                login_input_box.handle_event(event)
                click, _, _ = pg.mouse.get_pressed()
                if click == 1:
                    mouse = pg.mouse.get_pos()
                    if buttonRect.collidepoint(mouse):
                        login = login_input_box.text
                        client = Client(login, HOST, PORT)

                        user_registred = True
                        login_input_box.disable()
                        #client.post({"command":"start"})
                        time.sleep(0.3)
                pg.display.flip()
                continue

            elif user_registred:
                if is_game:
                    if is_my_step:
                        validMoves = gs.getValidMoves()
                        if event.type == pg.MOUSEBUTTONDOWN:
                            location = pg.mouse.get_pos()
                            col = location[0] // SQ_SIZE
                            row = location[1] // SQ_SIZE
                            if sqSelected == (row, col):
                                sqSelected = ()
                                playerClicks = []
                            else:
                                sqSelected = (row, col)
                                playerClicks.append(sqSelected)
                            if len(playerClicks) == 2:
                                move = Chess_Engine.Move(playerClicks[0], playerClicks[1], gs.board)

                                if move in validMoves:
                                    client.post({"step": playerClicks})

                                    gs.makeMove(move)
                                    moveMade = True
                                    is_my_step = False
                                    sqSelected = ()
                                    playerClicks = []

                                else:
                                    playerClicks = [sqSelected]
                    else:
                        headers, data = client.read()
                        is_my_step_server = data["is_my_step"]
                        is_my_step = is_my_step_server
                        print(is_my_step)
                        # headers, data = Client..read()
                        if headers["type"] == "json":
                            if data.get("step"):
                                step = data.get("step")
                                move = Chess_Engine.Move(step[0], step[1], gs.board)
                                gs.makeMove(move)
                    # elif event.type == pg.KEYDOWN:
                    #     if event.key == pg.K_z:
                    #         gs.undoMove()
                    #         moveMade = True

                    if moveMade:

                        moveMade = False


                    drawGameState(screen, gs)


                    clock.tick(MAX_FPS)
                    pg.display.flip()
                    continue
                    # button for begin game
                 #   pg.Rect()
                elif not is_past_matches_window and not is_past_matche_window:
                    screen.fill(WHITE)

                    button_begin_game, button_begin_game_text, button_begin_game_text_rect = draw_button((WIDTH_WINDOW / 4), (3 / 4) * HEIGHT_WINDOW, WIDTH_WINDOW / 2, 50, "Start")
                        # button for check all past games
                    button_get_matches, button_get_matches_text, button_get_matches_text_rect = draw_button((WIDTH_WINDOW / 4), (1 / 4) * HEIGHT_WINDOW, WIDTH_WINDOW / 2, 50,"Matches")
                        #pg.display.flip()
                    click, _, _ = pg.mouse.get_pressed()
                    if click == 1:
                        mouse = pg.mouse.get_pos()
                        if button_begin_game.collidepoint(mouse):
                            is_game = True
                            client.post({"command": "start"})
                            time.sleep(0.3)

                        if button_get_matches.collidepoint(mouse):
                            matches = client.get_req({"table": "matches"})
                            is_past_matches_window = True
                            #print(data)

                    pg.display.flip()
                    continue
                elif is_past_matches_window:

                    screen.fill(WHITE)


                    text_surface = mediumFont.render(f'Input num of game (from 0 to {len(matches)-1})', True, BLACK)
                    screen.blit(text_surface, (0, 0))
                    num_match_input_box.draw(screen)
                    num_match_input_box.handle_event(event)
                    # button for apply num match
                    button_watch_matche, button_watch_matche_text, button_watch_matche_text_rect = draw_button((WIDTH_WINDOW / 4), (3 / 4) * HEIGHT_WINDOW, WIDTH_WINDOW / 2, 50, "Watch")
                    click, _, _ = pg.mouse.get_pressed()
                    if click == 1:
                        mouse = pg.mouse.get_pos()
                        if button_watch_matche.collidepoint(mouse):
                            num_match = int(num_match_input_box.text)
                            is_past_matches_window = False
                            is_past_matche_window = True
                            gs_past_match = Chess_Engine.GameState()
                            matche = json.loads(matches[num_match]["steps"])
                            num_step = 0
                            # client.post({"command":"start"})
                            time.sleep(0.3)

                    pg.display.flip()
                elif is_past_matche_window:
                    #print("past match window")
                    #drawBoard(screen)
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_RIGHT:


                            try:
                                step = matche[num_step]
                            except:
                                is_past_matche_window = False
                                is_past_matches_window = False
                                is_game = False
                                time.sleep(3)

                            move = Chess_Engine.Move(step[0], step[1], gs_past_match.board)
                            gs_past_match.makeMove(move)
                            num_step += 1
                        if event.key == pg.K_LEFT:
                            num_step -= 1 if num_step else 0
                            if num_step:
                                gs_past_match.undoMove()
                            #drawGameState(gs_past_match)


                    drawGameState(screen, gs_past_match)
                    pg.display.flip()
if __name__ == '__main__':
    main()