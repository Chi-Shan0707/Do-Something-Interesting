class ChessPiece:
    def __init__(self, color, row, col):
        self.color = color  # 'red' 或 'black'
        self.row = row
        self.col = col
    
    def get_symbol(self):
        """返回棋子的显示符号"""
        raise NotImplementedError
    
    def is_valid_move(self, to_row, to_col, board):
        """检查移动是否合法"""
        raise NotImplementedError
    
    def is_in_bounds(self, row, col):
        """检查位置是否在棋盘内"""
        return 0 <= row <= 9 and 0 <= col <= 8

    def is_own_piece(self, row, col, board):
        """检查目标位置是否是己方棋子"""
        piece = board[row][col]
        return piece is not None and piece.color == self.color

    def checkmate(self,board):
        enemy_general_pos = None
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if isinstance(piece, General) and piece.color != self.color:
                    enemy_general_pos = (r, c)
                    break
            if enemy_general_pos:
                break
        to_row,to_col=enemy_general_pos
        if self.is_valid_move(to_row, to_col, board):
            return True

class General(ChessPiece):
    def get_symbol(self):
        return '帅' if self.color == 'red' else '将'
    
    def is_valid_move(self, to_row, to_col, board):
        if not self.is_in_bounds(to_row, to_col):
            return False
        # 目标位置不能是己方棋子
        if self.is_own_piece(to_row, to_col, board):
            return False
        # 九宫范围检查
        if self.color == 'red':
            # 红帅只能在 7-9行，3-5列
            if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                return False
        else:
            # 黑将只能在 0-2行，3-5列
            if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                return False
        # 移动规则：一次走一格，横竖均可
        row_diff = abs(to_row - self.row)
        col_diff = abs(to_col - self.col)
        if row_diff + col_diff != 1:
            return False
        # 将帅不能照面
        enemy_general_pos = None
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if isinstance(piece, General) and piece.color != self.color:
                    enemy_general_pos = (r, c)
                    break
            if enemy_general_pos:
                break
        if enemy_general_pos:
            e_row, e_col = enemy_general_pos
            if to_col == e_col:
                # 检查中间是否有棋子（当前将和对方将之间的行）
                start_row = min(self.row, e_row) + 1
                end_row = max(self.row, e_row) - 1
                for r in range(start_row, end_row + 1):
                    if board[r][to_col] is not None:
                        break
                else:
                    # 中间无棋子，照面非法
                    return False
        return True

class Advisor(ChessPiece):
    def get_symbol(self):
        return '仕' if self.color == 'red' else '士'

    def is_valid_move(self, to_row, to_col, board):
        # 1. 基础边界检查
        if not self.is_in_bounds(to_row, to_col):
            return False
        # 2. 目标位置不能是己方棋子
        if self.is_own_piece(to_row, to_col, board):
            return False

        # 3. 九宫范围检查（同将/帅）
        if self.color == 'red':
            if not (7 <= to_row <= 9 and 3 <= to_col <= 5):
                return False
        else:
            if not (0 <= to_row <= 2 and 3 <= to_col <= 5):
                return False

        # 4. 移动规则：斜走一格（横纵步长均为1）
        row_diff = abs(to_row - self.row)
        col_diff = abs(to_col - self.col)
        if row_diff != 1 or col_diff != 1:
            return False

        return True


class Elephant(ChessPiece):
    def get_symbol(self):
        return '相' if self.color == 'red' else '象'
    
    def is_valid_move(self, to_row, to_col, board):
        # 1. 基础边界检查
        if not self.is_in_bounds(to_row, to_col):
            return False
        # 2. 目标位置不能是己方棋子
        if self.is_own_piece(to_row, to_col, board):
            return False

        # 3. 不能过河检查
        if self.color == 'red':
            # 红相只能在 0-4行（河在4/5行之间）
            if to_row < 5:
                return False
        else:
            # 黑象只能在 5-9行
            if to_row > 4:
                return False

        # 4. 移动规则：走田字（横纵步长均为2）
        row_diff = abs(to_row - self.row)
        col_diff = abs(to_col - self.col)
        if row_diff != 2 or col_diff != 2:
            return False

        # 5. 象眼检查（田字中心位置必须无棋子）
        eye_row = (self.row + to_row) // 2
        eye_col = (self.col + to_col) // 2
        if board[eye_row][eye_col] is not None:
            return False

        return True

class Horse(ChessPiece):
    def get_symbol(self):
        return '马'
    
    def is_valid_move(self, to_row, to_col, board):
        # 在棋盘内
        if not self.is_in_bounds(to_row, to_col):
            return False
        # 目标位置不能是己方棋子
        if self.is_own_piece(to_row, to_col, board):
            return False
        # 移动规则：日字
        row_diff = abs(to_row - self.row)
        col_diff = abs(to_col - self.col)
        if row_diff+col_diff !=3 or col_diff==0 or row_diff==0:
            return False
        # 检查蹩马腿

        # 竖着走日
        if row_diff==2 and col_diff==1:
            middle=(to_row+self.row)//2
            if board[middle][to_col] is not None or board[middle][self.col] is not None:
                return False
        # 横着走日
        if row_diff==1 and col_diff==2:
            middle=(to_col+self.col)//2
            if board[to_row][middle] is not None or board[self.row][middle] is not None:
                return False
        return True

class Rook(ChessPiece):
    def get_symbol(self):
        return '车'
    
    def is_valid_move(self, to_row, to_col, board):
        # 在棋盘内
        if not self.is_in_bounds(to_row, to_col):
            return False
        # 目标位置不能是己方棋子
        if self.is_own_piece(to_row, to_col, board):
            return False
        # 移动规则：直线任意格
        if (to_row != self.row and to_col != self.col) or (to_row == self.row and to_col == self.col):
            return False
        # 检查路径上是否有其他棋子
        if self.row == to_row:
            # 横向移动
            start_col = min(self.col, to_col) + 1
            end_col = max(self.col, to_col) - 1
            for c in range(start_col, end_col + 1):
                if board[self.row][c] is not None:
                    return False
        else:
            # 纵向移动
            start_row = min(self.row, to_row) + 1
            end_row = max(self.row, to_row) - 1
            for r in range(start_row, end_row + 1):
                if board[r][self.col] is not None:
                    return False
        return True

class Cannon(ChessPiece):
    def get_symbol(self):
        return '炮'
    
    def is_valid_move(self, to_row, to_col, board):
        # 在棋盘内
        if not self.is_in_bounds(to_row, to_col):
            return False
        # 目标位置不能是己方棋子
        if self.is_own_piece(to_row, to_col, board):
            return False
        # 移动规则：直线，吃子时需要炮架
        if (to_row != self.row and to_col != self.col) or (to_row == self.row and to_col == self.col):
            return False
        # 统计路径上的棋子数
        if self.row == to_row:
            # 横向移动
            start_col = min(self.col, to_col) + 1
            end_col = max(self.col, to_col) - 1
            count=0
            for c in range(start_col, end_col + 1):
                if board[self.row][c] is not None:
                    count += 1

        else:
            # 纵向移动
            start_row = min(self.row, to_row) + 1
            end_row = max(self.row, to_row) - 1
            count=0
            for r in range(start_row, end_row + 1):
                if board[r][self.col] is not None:
                    count += 1

        # 移动或吃子规则
        # 吃子
        if board[to_row][to_col] is not None and count!=1:
            return False
        # 移动
        if board[to_row][to_col] is None and count!=0:
            return False

        return True

class Soldier(ChessPiece):
    def get_symbol(self):
        return '兵' if self.color == 'red' else '卒'
    
    def is_valid_move(self, to_row, to_col, board):
        # 在棋盘内
        if not self.is_in_bounds(to_row, to_col):
            return False
        # 目标位置不能是己方棋子
        if self.is_own_piece(to_row, to_col, board):
            return False
        # 红方向上移动，黑方向下移动
        row_diff = abs(to_row - self.row)
        col_diff = abs(to_col - self.col)
        if row_diff + col_diff != 1:
            return False
        # 红方不能后退
        if self.color == 'red':
            # 红兵：向前（行号减小），不能后退（行号增大）
            if to_row > self.row:
                return False  # 后退非法
            # 未过河（行号>4）：只能向前（列不变）
            if self.row >4 :
                return col_diff == 0  # 列必须不变，只能直行
            # 已过河（行号<=4）：可向前或左右（行不变或列变）
            else:
                return True
        else:
            # 黑卒：向前（行号增大），不能后退（行号减小）
            if to_row < self.row:
                return False  # 后退非法
            # 未过河（行号<5）：只能向前（列不变）
            if self.row <5:
                return col_diff == 0  # 列必须不变，只能直行
            # 已过河（行号>=5）：可向前或左右
            else:
                return True
        return True