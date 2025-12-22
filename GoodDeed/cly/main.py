from chess_board import ChessBoard

def main():
    print("欢迎来到命令行中国象棋！")
    print("坐标说明：使用字母a-i表示列，数字1-10表示行")
    print("例如：a1 表示左下角，i10 表示右上角")
    print("输入格式：起始位置 目标位置（如：a1 a2）")
    print("输入start开始游戏")
    print("输入quit退出游戏\n")
    
    chess_board = ChessBoard()
    running = True

    while running:

        try:
            user_input = input("\n请输入命令: ").strip().split()
            if not user_input:
                continue
            
            command = user_input[0].lower()
            
            # 如果命令是quit，退出程序。
            if command == 'quit':
                running = False
            # 如果命令是start，开始游戏。
            elif command == 'start':
                success, message = chess_board.start_game()
                print(message)
                if success:
                    chess_board.display()
            # 如果命令是stop，停止游戏。
            elif command == 'stop':
                success, message = chess_board.stop_game()
                print(message)
            # 如果命令是retract，执行悔棋。
            elif command == 'retract':
                success, message = chess_board.retract_move()
                print(message)
                if success:
                    chess_board.display()
            # 如果命令是save，保存游戏到指定文件。
            elif command == 'save':
                if len(user_input) < 2:
                    print("请指定保存文件名")
                else:
                    filename = user_input[1]
                    success, message = chess_board.save_game(filename)
                    print(message)
            # 如果命令是load，从指定文件加载游戏。
            elif command == 'load':
                if len(user_input) < 2:
                    print("请指定要加载的文件名")
                else:
                    filename = user_input[1]
                    success, message = chess_board.load_game(filename)
                    print(message)
                    if success:
                        chess_board.display()
            # 如果不是上述命令，认为输入的是移动命令，格式为字母+数字+空格+字母+数字。
            else:
                if len(user_input) != 2:
                    print("输入格式错误！请使用：起始位置 目标位置")
                    continue
                
                from_pos = chess_board.position_to_coords(user_input[0])
                to_pos = chess_board.position_to_coords(user_input[1])
                
                if from_pos is None or to_pos is None:
                    print("坐标格式错误！请使用字母a-i和数字1-10")
                    continue
                
                success, message = chess_board.move_piece(from_pos, to_pos)
                print(message)
                if success:
                    chess_board.display()
                    if chess_board.game_over:
                        print(f"游戏结束！{'红方' if chess_board.current_player == 'red' else '黑方'}获胜！")

            
        except KeyboardInterrupt:
            running = False
        except Exception as e:
            print(f"发生错误：{e}")

if __name__ == "__main__":
    main()