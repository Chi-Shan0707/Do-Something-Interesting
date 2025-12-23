
from pieces import Rook, Horse, Elephant, Advisor, General, Cannon, Soldier
import pickle
import os

class ChessBoard:
    def __init__(self):
        self.board = None
        self.current_player = 'red'  # 红方先行
        self.game_over = True # 标记游戏是否结束
        self.move_history = []  # 用于存储移动历史，实现悔棋功能
        
    def _initialize_board(self):
        """初始化棋盘"""
        # 使用二维列表表示棋盘，None表示空位
        board = [[None for _ in range(9)] for _ in range(10)]
        
        # 初始化红方棋子（下方）
        board[9][0] = Rook('red', 9, 0)      # 车
        board[9][1] = Horse('red', 9, 1)     # 马
        board[9][2] = Elephant('red', 9, 2)  # 相
        board[9][3] = Advisor('red', 9, 3)   # 士
        board[9][4] = General('red', 9, 4)   # 帅
        board[9][5] = Advisor('red', 9, 5)   # 士
        board[9][6] = Elephant('red', 9, 6)  # 相
        board[9][7] = Horse('red', 9, 7)     # 马
        board[9][8] = Rook('red', 9, 8)      # 车
        board[7][1] = Cannon('red', 7, 1)    # 炮
        board[7][7] = Cannon('red', 7, 7)    # 炮
        for i in range(0, 9, 2):
            board[6][i] = Soldier('red', 6, i)  # 兵
        
        # 初始化黑方棋子（上方）
        board[0][0] = Rook('black', 0, 0)      # 车
        board[0][1] = Horse('black', 0, 1)     # 马
        board[0][2] = Elephant('black', 0, 2)  # 象
        board[0][3] = Advisor('black', 0, 3)   # 仕
        board[0][4] = General('black', 0, 4)   # 将
        board[0][5] = Advisor('black', 0, 5)   # 仕
        board[0][6] = Elephant('black', 0, 6)  # 象
        board[0][7] = Horse('black', 0, 7)     # 马
        board[0][8] = Rook('black', 0, 8)      # 车
        board[2][1] = Cannon('black', 2, 1)    # 炮
        board[2][7] = Cannon('black', 2, 7)    # 炮
        for i in range(0, 9, 2):
            board[3][i] = Soldier('black', 3, i)  # 卒
            
        return board
    
    def display(self):
        """显示棋盘"""
        os.system('clear')
        print("\n  a   b   c   d   e   f   g   h   i")
        
        for i in range(10):
            if i ==0:
                row_str = f'{10}'
            else:
                row_str = f'{10-i} '
            for j in range(9):
                piece = self.board[i][j]
                if piece:
                    if piece.color == "red":
                        row_str += f"\033[31m{piece.get_symbol()}\033[0m"
                    else:
                        row_str += f"\033[34m{piece.get_symbol()}\033[0m"
                else:
                    row_str += "〇"
                row_str += "一"
            print(row_str[:-1])
            if i == 0 or i == 7:
                print("  丨  丨  丨  丨╲ 丨 ╱丨  丨  丨  丨")
            elif i == 1 or i == 8:
                print("  丨  丨  丨  丨╱ 丨 ╲丨  丨  丨  丨")
            elif i == 4:
                print("  丨      楚  河      汉  界      丨")
            elif i != 9:
                print("  丨  丨  丨  丨  丨  丨  丨  丨  丨")

        if not self.game_over:
            print(f"当前回合: {'红方' if self.current_player == 'red' else '黑方'}")

    def start_game(self):
        """开始游戏"""
        if self.game_over == False:
            return False, "游戏已经开始了"
        self.board = self._initialize_board()
        self.game_over = False
        self.move_history = []
        return True, "游戏开始！红方先行"

    def _get_general_pos(self, color):
        """获取指定颜色将/帅的位置"""
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if isinstance(piece, General) and piece.color == color:
                    return (row, col)
        return None  # 理论上不会出现

    def is_check(self, target_color):
        """检查指定颜色是否被将军（target_color是被将军的一方）"""
        # 获取被将军方的将/帅位置
        general_pos = self._get_general_pos(target_color)
        if not general_pos:
            return False
        g_row, g_col = general_pos

        # 检查对方所有棋子是否能攻击到将/帅
        attacker_color = 'black' if target_color == 'red' else 'red'
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece and piece.color == attacker_color:
                    # 检查该棋子是否能合法移动到将/帅位置
                    if piece.is_valid_move(g_row, g_col, self.board):
                        return True
        return False

    def is_checkmate(self, target_color):
        """检查指定颜色是否被将死"""
        # 先检查是否被将军
        if not self.is_check(target_color):
            return False

        # 遍历该方所有棋子，检查是否有合法移动能解除将军
        for from_row in range(10):
            for from_col in range(9):
                piece = self.board[from_row][from_col]
                if piece and piece.color == target_color:
                    # 遍历所有可能的目标位置
                    for to_row in range(10):
                        for to_col in range(9):
                            # 跳过己方棋子位置
                            if self.board[to_row][to_col] and self.board[to_row][to_col].color == target_color:
                                continue
                            # 检查移动是否合法
                            if piece.is_valid_move(to_row, to_col, self.board):
                                # 模拟移动，检查是否解除将军
                                # 保存原始状态
                                original_piece = self.board[to_row][to_col]
                                original_from = self.board[from_row][from_col]
                                original_piece_row = piece.row
                                original_piece_col = piece.col

                                # 执行模拟移动
                                self.board[to_row][to_col] = piece
                                self.board[from_row][from_col] = None
                                piece.row = to_row
                                piece.col = to_col

                                # 检查是否还被将军
                                check_after = self.is_check(target_color)

                                # 恢复原始状态
                                self.board[from_row][from_col] = original_from
                                self.board[to_row][to_col] = original_piece
                                piece.row = original_piece_row
                                piece.col = original_piece_col

                                # 如果有任何移动能解除将军，则不是将死
                                if not check_after:
                                    return False
        # 所有移动都无法解除将军，将死
        return True
    
    def stop_game(self):
        """停止游戏"""
        if self.game_over == True:
            return False, "游戏已经停止了"
        self.board = self._initialize_board()
        self.game_over = True
        self.move_history = []
        return True, "游戏停止"

    def move_piece(self, from_pos, to_pos):
        """移动棋子"""
        if self.game_over:
            return False, "游戏尚未开始，请输入start开始游戏"
            
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        piece = self.board[from_row][from_col]
        
        # 如果初始位置没有棋子，提示该位置没有棋子
        if self.board[from_row][from_col] is None:
            return False, "该位置没有棋子"
        # 如果初始位置是对方的棋子，提示不能移动对方的棋子
        if self.board[from_row][from_col].color != self.current_player:
            return False, "不能移动对方的棋子"
        # 如果移动不合法，提示移动不合法
        if not piece.is_valid_move(to_row, to_col, self.board):
            return False, "移动不符合棋子规则（如蹩马腿、象眼有子等）"
        # 记录移动前的状态，用于悔棋
        move_record = {
            'from_pos': (from_row, from_col),
            'to_pos': (to_row, to_col),
            'piece': piece,
            'captured_piece': self.board[to_row][to_col],
            'player': self.current_player
        }
        
        # 执行移动
        target_piece = self.board[to_row][to_col]
        # 如果目标位置是自己的棋子，提示不能吃掉自己的棋子
        if target_piece and target_piece.color == self.current_player:
            return False, "不能吃掉自己的棋子"

        # 移动棋子
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        piece.row = to_row
        piece.col = to_col

        if self.is_checkmate(self.current_player):
            # 移动不合法，恢复到移动之前，重新移动
            # 获取最后一步移动记录
            last_move = self.move_history.pop()
            from_row, from_col = last_move['from_pos']
            to_row, to_col = last_move['to_pos']
            piece = last_move['piece']
            captured_piece = last_move['captured_piece']
            player = last_move['player']

            # 恢复棋子位置
            self.board[from_row][from_col] = piece
            self.board[to_row][to_col] = captured_piece
            piece.row = from_row
            piece.col = from_col
            return False, "不能使自己被将军，请重新移动"

        enemy_color = 'black' if self.current_player == 'red' else 'red'
        if self.is_checkmate(enemy_color):
            self.game_over = True
            self.move_history.append(move_record)
            return True, f"将死！{self.current_player}方获胜"
        elif self.is_check(enemy_color):
            self.move_history.append(move_record)
            # 切换玩家
            self.current_player = enemy_color
            return True, "将军！"

        # 记录移动历史
        self.move_history.append(move_record)
        
        # 切换玩家
        self.current_player = 'black' if self.current_player == 'red' else 'red'
        
        return True, "移动成功"

    def position_to_coords(self, pos_str):
        """将字符串位置转换为坐标（如a10→(0,0)，i1→(9,8)）"""
        # 处理10行的情况（如a10）
        if len(pos_str) == 3 and pos_str[1:] == '10':
            col_char = pos_str[0]
            row_num = 10
        elif len(pos_str) == 2:
            col_char = pos_str[0]
            try:
                row_num = int(pos_str[1])
            except ValueError:
                return None
        else:
            return None

        # 列转换 (a-i → 0-8)
        col = ord(col_char.lower()) - ord('a')
        if col < 0 or col > 8:
            return None

        # 行转换 (1-10 → 9-0)
        row = 9 - (row_num - 1)
        if row < 0 or row > 9:
            return None

        return (row, col)


    def retract_move(self):
        """悔棋功能"""
        if self.game_over:
            return False, "游戏已结束，无法悔棋"
        if not self.move_history:
            return False, "没有可悔的步数"
        # 获取最后一步移动记录
        last_move = self.move_history.pop()
        from_row, from_col = last_move['from_pos']
        to_row, to_col = last_move['to_pos']
        piece = last_move['piece']
        captured_piece = last_move['captured_piece']
        player = last_move['player']

        # 恢复棋子位置
        self.board[from_row][from_col] = piece
        self.board[to_row][to_col] = captured_piece
        piece.row = from_row
        piece.col = from_col
        # 恢复玩家
        self.current_player = player
        return True, "悔棋成功"
    
    def save_game(self, filename):
        """保存游戏状态到文件"""
        if self.game_over:
            return False, "游戏尚未开始，无法保存"
            
        try:
            # 准备保存数据
            save_data = {
                'board': self.board,
                'current_player': self.current_player,
                'game_over': self.game_over,
                'move_history': self.move_history
            }

            with open(filename, 'wb') as file:
                pickle.dump(save_data, file)
            return True, f"游戏已成功保存到 {filename}"
        except Exception as e:
            return False, f"保存失败: {str(e)}"

    
    def load_game(self, filename):
        """从文件加载游戏状态"""
        try:
            # 恢复游戏状态
            with open(filename, 'rb') as f:
                save_data = pickle.load(f)

            # 恢复游戏状态
            self.board = save_data['board']
            self.current_player = save_data['current_player']
            self.game_over = save_data['game_over']
            self.move_history = save_data['move_history']

            return True, f"游戏已从 {filename} 成功加载"
        except FileNotFoundError:
            return False, "文件不存在"
        except Exception as e:
            return False, f"加载失败: {str(e)}"


